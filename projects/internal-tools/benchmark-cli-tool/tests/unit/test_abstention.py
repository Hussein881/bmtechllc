"""Tests for deterministic evidence acceptance rather than nearest-neighbor guesses."""

from __future__ import annotations

import pytest

from benchmark_cli import retrieval
from benchmark_cli.retrieval import (
    HybridSearchResult,
    meaningful_keyword_overlap,
    retrieve_evidence,
)
from benchmark_cli.storage.postgres import SearchChunk


def result(chunk_id: int, text: str, vector: float | None, fts: float | None) -> HybridSearchResult:
    return HybridSearchResult(SearchChunk(chunk_id, "source.txt", 0, text, {}, 1.0), 0.1, vector, fts)


@pytest.mark.unit
def test_keyword_overlap_counts_only_keyword_returned_evidence() -> None:
    candidates = (result(1, "HNSW latency provides eleven milliseconds", 0.9, 1.0),)
    assert meaningful_keyword_overlap("What HNSW latency?", candidates) == 2


@pytest.mark.unit
def test_retrieve_evidence_requires_both_similarity_and_keywords(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        retrieval,
        "search_docs",
        lambda *_args, **_kwargs: [result(1, "unrelated content", 0.91, 1.0)],
    )
    decision = retrieve_evidence("HNSW latency", min_cosine_similarity=0.30, min_keyword_overlap=1)
    assert decision.status == "no_relevant_information"
    assert decision.results == ()

    monkeypatch.setattr(
        retrieval,
        "search_docs",
        lambda *_args, **_kwargs: [result(1, "HNSW latency", 0.91, 1.0)],
    )
    decision = retrieve_evidence("HNSW latency", min_cosine_similarity=0.30, min_keyword_overlap=2)
    assert decision.status == "accepted"
    assert len(decision.results) == 1
