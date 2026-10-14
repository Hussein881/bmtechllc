"""Unit tests for retrieval-only Recall@5 and MRR calculations."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from benchmark_cli.config import GOLDEN_DATASET_PATH
from benchmark_cli.evaluation.dataset import load_golden_dataset, resolve_golden_dataset
from benchmark_cli.evaluation.metrics import (
    compare_retrieval_modes,
    comparison_markdown,
    evaluate_answers,
    evaluate_retrieval,
    recall_at_k,
    reciprocal_rank,
)
from benchmark_cli.evaluation.telemetry import CSV_COLUMNS, append_evaluation_log
from benchmark_cli.ingestion.chunk import chunk_units
from benchmark_cli.ingestion.clean import parse_by_type
from benchmark_cli.ingestion.pipeline import content_hash
from benchmark_cli.models import GoldenChunkReference, GoldenQuery
from benchmark_cli.paths import DOCUMENTS_DIR
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
    assert float(rows[0]["latency_ms"]) >= 0
    assert rows[0]["quality_recall_at_5"] == "1.0"
    assert rows[0]["quality_mrr"] == "1.0"


@pytest.mark.unit
def test_evaluation_log_migrates_existing_rows_to_latency_and_quality_schema() -> None:
    cases = [golden_query("q1", "one", [1], "lookup")]
    summary = evaluate_retrieval(cases, lambda _, __: [result(1)])
    legacy_columns = tuple(
        column
        for column in CSV_COLUMNS
        if column
        not in {
            "retrieval_mode",
            "latency_ms",
            "quality_recall_at_5",
            "quality_mrr",
        }
    )

    with TemporaryDirectory() as directory:
        path = Path(directory) / "evaluation.csv"
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=legacy_columns)
            writer.writeheader()
            writer.writerow({"question_id": "old-run", "retrieval_time_ms": "123.000"})
        append_evaluation_log(path, Path("golden.json"), summary)
        with path.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))

    assert tuple(rows[0]) == CSV_COLUMNS
    assert rows[0]["question_id"] == "old-run"
    assert rows[0]["latency_ms"] == ""
    assert rows[1]["quality_recall_at_5"] == "1.0"


@pytest.mark.unit
def test_comparison_reports_hybrid_improvements_in_before_after_table() -> None:
    cases = [golden_query("q1", "one", [1], "lookup")]
    comparison = compare_retrieval_modes(
        cases,
        vector_search=lambda _, __: [result(9)],
        hybrid_search=lambda _, __: [result(1)],
    )

    assert comparison.both_metrics_improved
    assert comparison.recall_at_5_delta == 1.0
    assert comparison.mrr_delta == 1.0
    table = comparison_markdown(comparison)
    assert "| Vector-only (before) | 0.000 | 0.000 |" in table
    assert "| Hybrid RRF (after) | 1.000 | 1.000 |" in table


@pytest.mark.unit
def test_seed_dataset_contains_thirty_queries_across_all_required_categories() -> None:
    cases = load_golden_dataset(GOLDEN_DATASET_PATH)

    assert len(cases) == 30
    assert [case.query_category for case in cases].count("lookup") == 8
    assert [case.query_category for case in cases].count("multi_chunk") == 8
    assert [case.query_category for case in cases].count("filter") == 7
    assert [case.query_category for case in cases].count("unanswerable") == 7
    assert all(case.required_answer_facts for case in cases if case.expected_chunks)


def test_company_fixture_hashes_match_every_golden_reference() -> None:
    cases = load_golden_dataset(GOLDEN_DATASET_PATH)
    expected = {
        (reference.source_file, reference.content_sha256)
        for case in cases
        for reference in case.expected_chunks
    }
    actual = {
        (path.name, content_hash(chunk.text))
        for path in DOCUMENTS_DIR.glob("company_*.txt")
        for chunk in chunk_units(parse_by_type(path))
    }
    assert expected <= actual


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


def test_answer_evaluation_scores_facts_and_abstention() -> None:
    from benchmark_cli.models import AnswerResponse, Citation

    cases = [
        GoldenQuery(
            question_id="answerable",
            question="one",
            expected_chunks=[GoldenChunkReference(source_file="source.txt", content_sha256="a" * 64)],
            query_category="lookup",
            required_answer_facts=["eleven milliseconds"],
        ),
        GoldenQuery(question_id="none", question="two", query_category="unanswerable"),
    ]

    def answer(question: str, **_: str) -> AnswerResponse:
        if question == "two":
            return AnswerResponse(
                status="no_relevant_information", answer="No relevant information.", confidence=0.0
            )
        return AnswerResponse(
            status="answered",
            answer="The result was eleven milliseconds.",
            confidence=0.9,
            citations=[Citation(source_file="source.txt", chunk_id=1, content_sha256="a" * 64, quote="eleven")],
        )

    summary = evaluate_answers(cases, answer)
    assert summary.abstention_f1 == 1.0
    assert summary.mean_answer_fact_coverage == 1.0
    assert summary.citation_validity_rate == 1.0
