"""Quiz model with JSON structure for flexible question schemas."""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, JSON
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Quiz(SQLModel, table=True):
    """Quiz definition stored as structured JSON for AI-generated content."""

    __tablename__ = "quizzes"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    title: str = Field(max_length=255, nullable=False, index=True)
    structure: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    def touch(self) -> None:
        self.updated_at = utc_now()
