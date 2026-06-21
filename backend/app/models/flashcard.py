"""Flashcard set and item models with spaced-repetition status."""

from datetime import datetime, timezone
from enum import IntEnum
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlmodel import Field, Relationship, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class FlashcardStatus(IntEnum):
    """Leitner box levels for spaced repetition (1 = new, 5 = mastered)."""

    NEW = 1
    LEARNING = 2
    REVIEW = 3
    FAMILIAR = 4
    MASTERED = 5


class FlashcardSet(SQLModel, table=True):
    """A named collection of flashcards tied to a user session."""

    __tablename__ = "flashcard_sets"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    session_id: UUID = Field(
        foreign_key="user_sessions.id",
        index=True,
        nullable=False,
    )
    title: str = Field(max_length=255, nullable=False)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    session: "UserSession" = Relationship(back_populates="flashcard_sets")
    items: list["FlashcardItem"] = Relationship(
        back_populates="flashcard_set",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class FlashcardItem(SQLModel, table=True):
    """Individual flashcard with front/back text and Leitner box status."""

    __tablename__ = "flashcard_items"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    set_id: UUID = Field(
        foreign_key="flashcard_sets.id",
        index=True,
        nullable=False,
    )
    front: str = Field(sa_column=Column(Text, nullable=False))
    back: str = Field(sa_column=Column(Text, nullable=False))
    status: FlashcardStatus = Field(
        default=FlashcardStatus.NEW,
        sa_column=Column(Integer, nullable=False, index=True),
    )

    flashcard_set: FlashcardSet = Relationship(back_populates="items")
