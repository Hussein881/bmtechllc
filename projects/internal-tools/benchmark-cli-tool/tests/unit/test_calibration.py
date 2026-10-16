"""Tests for deterministic selection of abstention cutoffs."""

from __future__ import annotations

import pytest

from benchmark_cli.evaluation.calibration import calibrate_abstention
from benchmark_cli.models import GoldenChunkReference, GoldenQuery
from benchmark_cli.retrieval import HybridSearchResult
from benchmark_cli.storage.postgres import SearchChunk


def _result(score: float, text: str) -> HybridSearchResult:
    return HybridSearchResult(SearchChunk(1, "source.txt", 0, text, {}, 1.0), 0.1, score, 1.0)


@pytest.mark.unit
def test_calibration_maximizes_answerable_acceptance_under_near_miss_limit() -> None:
    cases = [
        GoldenQuery(question_id="yes", question="HNSW latency", query_category="lookup", expected_chunks=[GoldenChunkReference(source_file="source.txt", content_sha256="a" * 64)]),
        GoldenQuery(question_id="no", question="HNSW budget", query_category="unanswerable"),
    ]
    responses = {"HNSW latency": [_result(0.60, "HNSW latency")], "HNSW budget": [_result(0.35, "HNSW")]} 
    chosen = calibrate_abstention(cases, lambda question, _top_k, **_: responses[question], cosine_candidates=(0.30, 0.50), keyword_candidates=(1,))
    assert chosen.min_cosine_similarity == 0.50
    assert chosen.answerable_acceptance_rate == 1.0
    assert chosen.near_miss_false_accept_rate == 0.0
