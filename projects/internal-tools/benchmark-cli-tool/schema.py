"""Structured response schemas used by the Q&A application."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class QAResponse(BaseModel):
    """A document-grounded answer with confidence and supporting quotation."""

    answer: str
    confidence: float = Field(ge=0.0, le=1.0)
    source_quote: str


class ChunkMetadata(BaseModel):
    """Validated metadata persisted with one vector-RAG document chunk."""

    source_type: Literal["discord", "transcript", "policy_doc"]
    date: str
    ingested_at: str
    section: str | None = None
    speakers: list[str] = Field(default_factory=list)
    channel: str | None = None
    date_start: str | None = None
    date_end: str | None = None
    meeting: str | None = None
    message_count: int | None = Field(default=None, ge=1)
    split_unit: bool = False
    embed_prefix: str = ""

    @model_validator(mode="after")
    def validate_source_fields(self) -> "ChunkMetadata":
        """Require the source-specific fields that make retrieval locations meaningful."""
        if self.source_type == "discord" and (not self.channel or not self.date_end):
            raise ValueError("discord chunk metadata requires channel and date_end.")
        if self.source_type == "transcript" and not self.meeting:
            raise ValueError("transcript chunk metadata requires meeting.")
        if self.source_type == "policy_doc" and not self.section:
            raise ValueError("policy_doc chunk metadata requires section.")
        return self
