"""Preprocessing utilities for normalized ingestion and content hashing."""

from __future__ import annotations

import hashlib
from pathlib import Path


def normalize_text(text: str) -> str:
    """Normalize text before hashing and chunking."""
    if not text:
        return ""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if normalized.startswith("\ufeff"):
        normalized = normalized.lstrip("\ufeff")
    return "\n".join(line.rstrip() for line in normalized.split("\n")).strip()


def normalized_content_hash(text: str) -> str:
    """Return SHA-256 of normalized content."""
    normalized = normalize_text(text)
    return hashlib.sha256(normalized.encode("utf-8", errors="replace")).hexdigest()


def sniff_loader_key(path: Path, sample_text: str) -> str | None:
    """Best-effort fallback loader choice for ambiguous extensions."""
    suffix = path.suffix.lower()
    if suffix:
        return None

    sample = sample_text.strip()
    lowered = sample.lower()
    if sample.startswith("#"):
        return "markdown"
    if any(tok in lowered for tok in ("error", "warn", "traceback", "failed")):
        return "log"
    if any(tok in sample for tok in ("def ", "class ", "import ", "{")):
        return "code"
    return "text"
