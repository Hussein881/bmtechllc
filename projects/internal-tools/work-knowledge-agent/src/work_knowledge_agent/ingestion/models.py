"""Shared ingestion data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class LoadedDocument:
    """Normalized document payload returned by loaders."""

    source_path: Path
    text: str
    size_bytes: int
    media_type: str
    structural_hints: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class QuarantineRecord:
    """Represents an input that could not be safely ingested."""

    source_file: str
    reason: str
    detail: str
    stage: str
    content_hash: str = ""
