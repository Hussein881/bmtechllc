"""Golden retrieval-dataset loading and validation."""

from __future__ import annotations

import json
from pathlib import Path

from ..models import GoldenQuery


def load_golden_dataset(path: Path) -> list[GoldenQuery]:
    """Load a JSON list of validated retrieval-only golden queries."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Golden dataset must be a JSON list.")
    cases = [GoldenQuery.model_validate(item) for item in payload]
    ids = [case.question_id for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Golden dataset question_id values must be unique.")
    return cases
