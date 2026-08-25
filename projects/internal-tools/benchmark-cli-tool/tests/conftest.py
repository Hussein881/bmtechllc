"""Shared pytest fixtures for deterministic local test data."""

from __future__ import annotations

from pathlib import Path

import pytest

from benchmark_cli import retrieval


@pytest.fixture
def document_library(monkeypatch: pytest.MonkeyPatch) -> Path:
    """Use the checked-in, sanitized document fixtures for retrieval tests."""
    path = Path(__file__).parent / "fixtures" / "documents"
    monkeypatch.setattr(retrieval, "DOCUMENTS_DIR", path)
    return path
