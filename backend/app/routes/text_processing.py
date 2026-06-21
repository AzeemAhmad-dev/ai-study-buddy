"""Core text processing routes powered by Gemini structured output."""

from __future__ import annotations

import os
import shutil
import tempfile
import time
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from google import genai
from pydantic import BaseModel, Field, field_validator
from sqlmodel import Session

from app.config import Settings, get_settings
from app.database import get_session
from app.models.flashcard import FlashcardItem, FlashcardSet, FlashcardStatus
from app.models.session import UserSession
from app.services.gemini import create_gemini_client, generate_structured_content, generate_text

router = APIRouter(prefix="/text", tags=["text-processing"])

SUMMARIZE_SYSTEM_INSTRUCTION = """You are an expert academic tutor creating concise study guides.

Transform the provided source material into a structured study guide using Markdown with:
1. A top-level title derived from the content.
2. Clear section headings (##) for major themes.
3. Bold bullet points (**•** or - with **bold key terms**) under each section.
4. A final section titled "## ELI5 — Explain Like I'm 5" that restates the core concept in simple language and includes one vivid, easy-to-understand analogy.

Rules:
- Be accurate and faithful to the source; do not invent facts.
- Prefer clarity over length.
- Use Markdown formatting only; do not wrap the answer in JSON or code fences."""

FLASHCARD_SYSTEM_INSTRUCTION = """You are an expert study coach generating high-quality flashcards.

Extract the most important terms, concepts, definitions, and cause-effect relationships from the source text.
Each card must have a concise front (term/concept/question) and a clear back (definition/explanation/answer).
Avoid duplicate cards and trivial details."""

QUIZ_SYSTEM_INSTRUCTION = """You are an expert educator creating multiple-choice quizzes.

Generate challenging but fair questions that test understanding, not rote memorization.
Each question must have exactly four distinct answer options labeled implicitly as A, B, C, and D in order.
The correct_answer field must exactly match one of the four option strings.
Include a brief explanation for why the correct answer is right."""


class SummarizeResponse(BaseModel):
    study_guide: str
    model: str


class GeminiFlashcardItem(BaseModel):
    front: str = Field(min_length=1, description="Term or concept on the front of the card.")
    back: str = Field(min_length=1, description="Definition or explanation on the back.")


class GeminiFlashcardResponse(BaseModel):
    cards: list[GeminiFlashcardItem] = Field(min_length=1)


class SavedFlashcardItem(BaseModel):
    id: UUID
    front: str
    back: str
    status: FlashcardStatus


class FlashcardsResponse(BaseModel):
    session_id: UUID
    set_id: UUID
    title: str
    cards_created: int
    cards: list[SavedFlashcardItem]
    model: str


class GeminiQuizQuestion(BaseModel):
    question_id: int = Field(ge=1)
    question_text: str = Field(min_length=1)
    options: list[str] = Field(min_length=4, max_length=4)
    correct_answer: str = Field(min_length=1)
    explanation: str = Field(min_length=1)

    @field_validator("options")
    @classmethod
    def validate_options(cls, options: list[str]) -> list[str]:
        cleaned = [option.strip() for option in options if option.strip()]
        if len(cleaned) != 4:
            raise ValueError("Each question must contain exactly four non-empty options.")
        return cleaned

    @field_validator("correct_answer")
    @classmethod
    def validate_correct_answer(cls, correct_answer: str, info) -> str:
        options = info.data.get("options") or []
        if options and correct_answer not in options:
            raise ValueError("correct_answer must match one of the provided options.")
        return correct_answer


class GeminiQuizResponse(BaseModel):
    quiz_title: str = Field(min_length=1)
    questions: list[GeminiQuizQuestion] = Field(min_length=1)


def get_gemini_client(settings: Settings = Depends(get_settings)) -> genai.Client:
    return create_gemini_client(settings)


def _resolve_or_create_session(db: Session, session_id: UUID | None) -> UserSession:
    if session_id is not None:
        user_session = db.get(UserSession, session_id)
        if user_session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User session '{session_id}' was not found.",
            )
        return user_session

    user_session = UserSession()
    db.add(user_session)
    db.flush()
    return user_session


def _derive_flashcard_set_title(
    requested_title: str | None,
    cards: list[GeminiFlashcardItem],
) -> str:
    if requested_title and requested_title.strip():
        return requested_title.strip()[:255]

    first_front = cards[0].front.strip()
    if len(first_front) <= 60:
        return f"Flashcards: {first_front}"[:255]
    return f"Flashcards: {first_front[:57]}..."[:255]


@router.post("/summarize", response_model=SummarizeResponse)
def summarize_text(
    text: str | None = Form(None),
    file: UploadFile | None = File(None),
    max_sections: int = Form(6, ge=2, le=12),
    model: str = Form("gemini-1.5-flash"),
    settings: Settings = Depends(get_settings),
    client: genai.Client = Depends(get_gemini_client),
) -> SummarizeResponse:
    """Summarize multimodal content into a structured Markdown study guide."""
    if not text and not file:
        raise HTTPException(status_code=400, detail="Provide either 'text' or 'file'.")

    temp_file_path = ""
    file_ref = None

    try:
        contents = []
        if file:
            _, ext = os.path.splitext(file.filename or "")
            fd, temp_file_path = tempfile.mkstemp(suffix=ext)
            
            # OOM Patch: Stream to disk safely
            with os.fdopen(fd, "wb") as f:
                shutil.copyfileobj(file.file, f)
            
            file_ref = client.files.upload(file=temp_file_path)
            
            # Race Condition Patch: Poll until Google finishes processing
            while file_ref.state.name == "PROCESSING":
                time.sleep(2)
                file_ref = client.files.get(name=file_ref.name)

            if file_ref.state.name == "FAILED":
                raise HTTPException(status_code=400, detail="Document processing failed on Google servers.")

            contents.append(file_ref)
            
        if text:
            contents.append(text)

        prompt_instructions = (
            "Create a study guide from the provided material. "
            f"Use at most {max_sections} major sections before the ELI5 section."
        )
        contents.append(prompt_instructions)

        study_guide = generate_text(
            client,
            model=model,
            contents=contents,
            settings=settings,
            system_instruction=SUMMARIZE_SYSTEM_INSTRUCTION,
            temperature=0.4,
        )

        return SummarizeResponse(study_guide=study_guide, model=model)
    finally:
        if file_ref:
            try:
                client.files.delete(name=file_ref.name)
            except Exception:
                pass
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass


@router.post("/flashcards", response_model=FlashcardsResponse)
def generate_flashcards(
    text: str | None = Form(None),
    file: UploadFile | None = File(None),
    session_id: UUID | None = Form(None),
    set_title: str | None = Form(None),
    max_cards: int = Form(12, ge=1, le=40),
    model: str = Form("gemini-1.5-flash"),
    settings: Settings = Depends(get_settings),
    client: genai.Client = Depends(get_gemini_client),
    db: Session = Depends(get_session),
) -> FlashcardsResponse:
    """Generate flashcards with Gemini structured output and persist them."""
    if not text and not file:
        raise HTTPException(status_code=400, detail="Provide either 'text' or 'file'.")

    temp_file_path = ""
    file_ref = None

    try:
        contents = []
        if file:
            _, ext = os.path.splitext(file.filename or "")
            fd, temp_file_path = tempfile.mkstemp(suffix=ext)
            
            # OOM Patch: Stream to disk safely
            with os.fdopen(fd, "wb") as f:
                shutil.copyfileobj(file.file, f)
                
            file_ref = client.files.upload(file=temp_file_path)
            
            # Race Condition Patch: Poll until Google finishes processing
            while file_ref.state.name == "PROCESSING":
                time.sleep(2)
                file_ref = client.files.get(name=file_ref.name)

            if file_ref.state.name == "FAILED":
                raise HTTPException(status_code=400, detail="Document processing failed on Google servers.")

            contents.append(file_ref)
            
        if text:
            contents.append(text)

        prompt_instructions = f"Create up to {max_cards} flashcards from the provided material."
        contents.append(prompt_instructions)

        parsed = generate_structured_content(
            client,
            model=model,
            contents=contents,
            settings=settings,
            response_schema=GeminiFlashcardResponse,
            system_instruction=FLASHCARD_SYSTEM_INSTRUCTION,
            temperature=0.3,
        )

        if not parsed.cards:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Gemini returned an empty flashcard set.",
            )

        cards = parsed.cards[: max_cards]
        user_session = _resolve_or_create_session(db, session_id)
        user_session.touch()

        title = _derive_flashcard_set_title(set_title, cards)
        flashcard_set = FlashcardSet(session_id=user_session.id, title=title)
        db.add(flashcard_set)
        db.flush()

        saved_items: list[SavedFlashcardItem] = []
        for card in cards:
            item = FlashcardItem(
                set_id=flashcard_set.id,
                front=card.front.strip(),
                back=card.back.strip(),
                status=FlashcardStatus.NEW,
            )
            db.add(item)
            db.flush()
            saved_items.append(
                SavedFlashcardItem(
                    id=item.id,
                    front=item.front,
                    back=item.back,
                    status=item.status,
                )
            )

        db.refresh(flashcard_set)
        db.refresh(user_session)

        return FlashcardsResponse(
            session_id=user_session.id,
            set_id=flashcard_set.id,
            title=flashcard_set.title,
            cards_created=len(saved_items),
            cards=saved_items,
            model=model,
        )
    finally:
        if file_ref:
            try:
                client.files.delete(name=file_ref.name)
            except Exception:
                pass
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass


@router.post("/quiz", response_model=GeminiQuizResponse)
def generate_quiz(
    text: str | None = Form(None),
    file: UploadFile | None = File(None),
    topic: str | None = Form(None),
    question_count: int = Form(5, ge=1, le=20),
    model: str = Form("gemini-1.5-flash"),
    settings: Settings = Depends(get_settings),
    client: genai.Client = Depends(get_gemini_client),
) -> GeminiQuizResponse:
    """Generate a multiple-choice quiz using Gemini structured output."""
    if not text and not file and not topic:
        raise HTTPException(status_code=400, detail="Provide either 'text', 'file', or 'topic'.")

    temp_file_path = ""
    file_ref = None

    try:
        contents = []
        if file:
            _, ext = os.path.splitext(file.filename or "")
            fd, temp_file_path = tempfile.mkstemp(suffix=ext)
            
            # OOM Patch: Stream to disk safely
            with os.fdopen(fd, "wb") as f:
                shutil.copyfileobj(file.file, f)
                
            file_ref = client.files.upload(file=temp_file_path)
            
            # Race Condition Patch: Poll until Google finishes processing
            while file_ref.state.name == "PROCESSING":
                time.sleep(2)
                file_ref = client.files.get(name=file_ref.name)

            if file_ref.state.name == "FAILED":
                raise HTTPException(status_code=400, detail="Document processing failed on Google servers.")

            contents.append(file_ref)
            
        if text:
            contents.append(text)
            
        if topic and not text and not file:
            contents.append(f"About the topic: {topic}")

        prompt_instructions = f"Create exactly {question_count} multiple-choice questions based on the provided reference material."
        contents.append(prompt_instructions)

        parsed = generate_structured_content(
            client,
            model=model,
            contents=contents,
            settings=settings,
            response_schema=GeminiQuizResponse,
            system_instruction=QUIZ_SYSTEM_INSTRUCTION,
            temperature=0.5,
        )

        if len(parsed.questions) > question_count:
            parsed = GeminiQuizResponse(
                quiz_title=parsed.quiz_title,
                questions=parsed.questions[: question_count],
            )

        return parsed
    finally:
        if file_ref:
            try:
                client.files.delete(name=file_ref.name)
            except Exception:
                pass
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass