"""Unit tests for retrieval-only Recall@5 and MRR calculations."""

from __future__ import annotations

import pytest

from benchmark_cli.config import GOLDEN_DATASET_PATH
from benchmark_cli.evaluation.dataset import load_golden_dataset
from benchmark_cli.evaluation.metrics import evaluate_retrieval, recall_at_k, reciprocal_rank
from benchmark_cli.models import GoldenQuery
from benchmark_cli.retrieval import HybridSearchResult
from benchmark_cli.storage.postgres import SearchChunk


def result(chunk_id: int) -> HybridSearchResult:
    return HybridSearchResult(SearchChunk(chunk_id, "source.txt", 0, "text", {}, 1.0), 0.1)


@pytest.mark.unit
def test_recall_at_5_counts_all_expected_chunks_for_multi_chunk_queries() -> None:
    assert recall_at_k([10, 20, 30, 40, 50], [20, 40]) == 1.0
    assert recall_at_k([10, 20, 30, 40, 50], [20, 99]) == 0.5


@pytest.mark.unit
def test_mrr_uses_the_first_relevant_chunk_rank() -> None:
    assert reciprocal_rank([5, 8, 12], [12, 8]) == pytest.approx(1 / 2)
    assert reciprocal_rank([5, 8, 12], [99]) == 0.0


@pytest.mark.unit
def test_evaluation_aggregates_relevant_queries_and_keeps_unanswerable_cases() -> None:
    cases = [
        GoldenQuery(question_id="q1", question="one", expected_chunk_ids=[1], query_category="lookup"),
        GoldenQuery(question_id="q2", question="two", expected_chunk_ids=[2, 3], query_category="multi_chunk"),
        GoldenQuery(question_id="q3", question="none", expected_chunk_ids=[], query_category="unanswerable"),
    ]
    results = {"one": [result(1)], "two": [result(9), result(2)], "none": [result(7)]}

    summary = evaluate_retrieval(cases, lambda question, _: results[question])

    assert summary.recall_at_5 == pytest.approx(0.75)
    assert summary.mrr == pytest.approx(0.75)
    assert summary.relevant_queries == 2
    assert summary.unanswerable_queries == 1
    assert summary.per_query[2].recall_at_5 is None


@pytest.mark.unit
def test_seed_dataset_contains_thirty_queries_across_all_required_categories() -> None:
    cases = load_golden_dataset(GOLDEN_DATASET_PATH)

    assert len(cases) == 30
    assert [case.query_category for case in cases].count("lookup") == 10
    assert [case.query_category for case in cases].count("multi_chunk") == 10
    assert [case.query_category for case in cases].count("unanswerable") == 10
