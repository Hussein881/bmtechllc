"""Validated ingestion metadata and retrieval-evaluation dataset models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ChunkMetadata(BaseModel):
    """Provenance retained for a persisted document chunk."""

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
    def validate_source_fields(self) -> ChunkMetadata:
        if self.source_type == "discord" and (not self.channel or not self.date_end):
            raise ValueError("discord chunk metadata requires channel and date_end.")
        if self.source_type == "transcript" and not self.meeting:
            raise ValueError("transcript chunk metadata requires meeting.")
        if self.source_type == "policy_doc" and not self.section:
            raise ValueError("policy_doc chunk metadata requires section.")
        return self


QueryCategory = Literal["lookup", "multi_chunk", "unanswerable"]


class GoldenQuery(BaseModel):
    """One retrieval-only evaluation query with stable database chunk identifiers."""

    question_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    expected_chunk_ids: list[int] = Field(default_factory=list)
    query_category: QueryCategory

    @model_validator(mode="after")
    def validate_expected_chunks(self) -> GoldenQuery:
        if self.query_category == "unanswerable" and self.expected_chunk_ids:
            raise ValueError("unanswerable queries must not specify expected_chunk_ids.")
        if self.query_category == "lookup" and len(self.expected_chunk_ids) != 1:
            raise ValueError("lookup queries require exactly one expected chunk id.")
        if self.query_category == "multi_chunk" and len(set(self.expected_chunk_ids)) < 2:
            raise ValueError("multi_chunk queries require at least two distinct expected chunk ids.")
        return self
