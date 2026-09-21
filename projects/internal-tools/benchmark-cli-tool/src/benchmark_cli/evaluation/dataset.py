"""Golden retrieval-dataset loading and validation."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from ..models import GoldenChunkReference, GoldenQuery
from ..storage.postgres import resolve_chunk_references

ChunkIdResolver = Callable[[Sequence[GoldenChunkReference]], Mapping[tuple[str, str], int]]


def load_golden_dataset(path: Path) -> list[GoldenQuery]:
    """Load a JSON list of validated, durable retrieval-only golden queries."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Golden dataset must be a JSON list.")
    cases = [GoldenQuery.model_validate(item) for item in payload]
    ids = [case.question_id for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Golden dataset question_id values must be unique.")
    return cases


def resolve_golden_dataset(
    cases: Sequence[GoldenQuery], *, resolver: ChunkIdResolver = resolve_chunk_references
) -> list[GoldenQuery]:
    """Resolve stable source-content references to the current database IDs."""
    references = [reference for case in cases for reference in case.expected_chunks]
    resolved_ids = resolver(references)
    return [
        case.model_copy(
            update={
                "expected_chunk_ids": [
                    resolved_ids[(reference.source_file, reference.content_sha256)]
                    for reference in case.expected_chunks
                ]
            }
        )
        for case in cases
    ]
