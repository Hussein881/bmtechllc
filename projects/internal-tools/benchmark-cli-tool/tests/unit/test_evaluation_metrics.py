"""Unit tests for retrieval-only Recall@5 and MRR calculations."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from benchmark_cli.config import GOLDEN_DATASET_PATH
from benchmark_cli.evaluation.dataset import load_golden_dataset, resolve_golden_dataset
from benchmark_cli.evaluation.metrics import evaluate_retrieval, recall_at_k, reciprocal_rank
from benchmark_cli.evaluation.telemetry import CSV_COLUMNS, append_evaluation_log
from benchmark_cli.models import GoldenChunkReference, GoldenQuery
from benchmark_cli.retrieval import HybridSearchResult
from benchmark_cli.storage.postgres import SearchChunk


def result(chunk_id: int, vector_score: float | None = 0.9) -> HybridSearchResult:
    return HybridSearchResult(
        SearchChunk(chunk_id, "source.txt", 0, "text", {}, 1.0), 0.1, vector_score=vector_score
    )


def golden_query(
    question_id: str, question: str, expected_ids: list[int], query_category: str
) -> GoldenQuery:
    return GoldenQuery(
        question_id=question_id,
        question=question,
        expected_chunks=[
            GoldenChunkReference(source_file="source.txt", content_sha256=f"{chunk_id:064x}")
            for chunk_id in expected_ids
        ],
        expected_chunk_ids=expected_ids,
        query_category=query_category,
    )


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
        golden_query("q1", "one", [1], "lookup"),
        golden_query("q2", "two", [2, 3], "multi_chunk"),
        golden_query("q3", "none", [], "unanswerable"),
    ]
    results = {"one": [result(1)], "two": [result(9), result(2)], "none": [result(7)]}

    summary = evaluate_retrieval(cases, lambda question, _: results[question])

    assert summary.recall_at_5 == pytest.approx(0.75)
    assert summary.mrr == pytest.approx(0.75)
    assert summary.relevant_queries == 2
    assert summary.unanswerable_queries == 1
    assert summary.per_query[2].recall_at_5 is None
    assert summary.per_query[0].retrieval_time_ms >= 0
    assert summary.per_query[0].top_chunk_vector_similarity_scores == (0.9,)


@pytest.mark.unit
def test_evaluation_log_appends_query_metrics_with_blank_generation_time() -> None:
    cases = [golden_query("q1", "one", [1], "lookup")]
    summary = evaluate_retrieval(cases, lambda _, __: [result(1, vector_score=0.81)])

    with TemporaryDirectory() as directory:
        path = Path(directory) / "evaluation.csv"
        append_evaluation_log(path, Path("golden.json"), summary)
        append_evaluation_log(path, Path("golden.json"), summary)
        with path.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))

    assert tuple(rows[0]) == CSV_COLUMNS
    assert len(rows) == 2
    assert rows[0]["run_id"] != rows[1]["run_id"]
    assert rows[0]["generation_time_ms"] == ""
    assert float(rows[0]["retrieval_time_ms"]) >= 0
    assert json.loads(rows[0]["top_chunk_vector_similarity_scores"]) == [0.81]
    assert rows[0]["recall_at_5"] == "1.0"
    assert rows[0]["run_recall_at_5"] == "1.0"


@pytest.mark.unit
def test_seed_dataset_contains_thirty_queries_across_all_required_categories() -> None:
    cases = load_golden_dataset(GOLDEN_DATASET_PATH)

    assert len(cases) == 30
    assert [case.query_category for case in cases].count("lookup") == 10
    assert [case.query_category for case in cases].count("multi_chunk") == 10
    assert [case.query_category for case in cases].count("unanswerable") == 10


@pytest.mark.unit
def test_dataset_resolves_durable_references_to_current_database_ids() -> None:
    reference = GoldenChunkReference(source_file="source.txt", content_sha256="a" * 64)
    case = GoldenQuery(
        question_id="q1",
        question="one",
        expected_chunks=[reference],
        query_category="lookup",
    )

    resolved = resolve_golden_dataset(
        [case], resolver=lambda references: {(item.source_file, item.content_sha256): 42 for item in references}
    )

    assert resolved[0].expected_chunk_ids == [42]
    assert case.expected_chunk_ids == []
