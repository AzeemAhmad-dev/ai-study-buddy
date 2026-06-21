"""AI-related API routes powered by Google Gemini."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from google import genai
from google.genai import errors as genai_errors
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.config import Settings, get_settings
from app.database import get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


class ChatMessage(BaseModel):
    role: str = Field(..., examples=["user", "model"])
    content: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1)
    system_instruction: str | None = Field(
        default="You are a helpful AI study buddy. Explain concepts clearly and encourage active learning.",
    )


class ChatResponse(BaseModel):
    reply: str
    model: str


def get_gemini_client(settings: Settings = Depends(get_settings)) -> genai.Client:
    return genai.Client(api_key=settings.gemini_api_key)


@router.get("/health")
def ai_health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    """Verify AI route wiring and configured model."""
    return {
        "status": "ok",
        "model": settings.gemini_model,
    }


@router.post("/chat", response_model=ChatResponse)
def chat_with_study_buddy(
    payload: ChatRequest,
    settings: Settings = Depends(get_settings),
    client: genai.Client = Depends(get_gemini_client),
    _session: Session = Depends(get_session),
) -> ChatResponse:
    """Send a chat turn to Gemini and return the model response."""
    contents: list[dict[str, Any]] = [
        {"role": message.role, "parts": [{"text": message.content}]}
        for message in payload.messages
    ]

    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=contents,
            config={
                "system_instruction": payload.system_instruction,
            },
        )
    except genai_errors.ClientError as exc:
        logger.exception("Gemini API client error")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini API error: {exc}",
        ) from exc
    except genai_errors.ServerError as exc:
        logger.exception("Gemini API server error")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini service is temporarily unavailable.",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error calling Gemini")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating a response.",
        ) from exc

    reply_text = (response.text or "").strip()
    if not reply_text:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini returned an empty response.",
        )

    return ChatResponse(reply=reply_text, model=settings.gemini_model)
