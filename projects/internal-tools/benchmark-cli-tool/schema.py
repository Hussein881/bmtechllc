"""Structured response schemas used by the Q&A application."""

from __future__ import annotations

from pydantic import BaseModel, Field


class QAResponse(BaseModel):
    """A document-grounded answer with confidence and supporting quotation."""

    answer: str
    confidence: float = Field(ge=0.0, le=1.0)
    source_quote: str
