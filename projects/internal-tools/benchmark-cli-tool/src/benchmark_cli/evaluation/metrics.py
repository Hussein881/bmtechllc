"""Metrics for evaluating retrieval results without answer generation."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from time import perf_counter
from typing import Any

from ..models import GoldenQuery
from ..retrieval import HybridSearchResult


def recall_at_k(retrieved_ids: Sequence[int], expected_ids: Sequence[int], k: int = 5) -> float:
    """Return the fraction of relevant chunks present in the first *k* results."""
    if k < 1:
        raise ValueError("k must be at least 1.")
    relevant = set(expected_ids)
    if not relevant:
        raise ValueError("Recall is undefined for a query with no expected chunks.")
    return len(relevant.intersection(retrieved_ids[:k])) / len(relevant)


def reciprocal_rank(
    retrieved_ids: Sequence[int], expected_ids: Sequence[int], k: int = 5
) -> float:
    """Return the reciprocal rank of the first relevant chunk in the first *k* results."""
    if k < 1:
        raise ValueError("k must be at least 1.")
    relevant = set(expected_ids)
    for rank, chunk_id in enumerate(retrieved_ids[:k], start=1):
        if chunk_id in relevant:
            return 1.0 / rank
    return 0.0


@dataclass(frozen=True, slots=True)
class QueryMetrics:
    """Search-only metrics and returned identifiers for one golden query."""

    question_id: str
    query_category: str
    retrieved_chunk_ids: tuple[int, ...]
    retrieval_time_ms: float
    generation_time_ms: float | None
    top_chunk_rrf_scores: tuple[float, ...]
    top_chunk_vector_similarity_scores: tuple[float | None, ...]
    recall_at_5: float | None
    reciprocal_rank: float | None


@dataclass(frozen=True, slots=True)
class EvaluationSummary:
    """Aggregate retrieval metrics; unanswerable cases are retained but excluded from R@5/MRR."""

    total_queries: int
    relevant_queries: int
    unanswerable_queries: int
    recall_at_5: float
    mrr: float
    per_query: tuple[QueryMetrics, ...]

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["per_query"] = list(payload["per_query"])
        return payload


@dataclass(frozen=True, slots=True)
class RetrievalComparison:
    """A directly comparable vector-only baseline and hybrid measurement."""

    vector_only: EvaluationSummary
    hybrid: EvaluationSummary

    @property
    def recall_at_5_delta(self) -> float:
        return self.hybrid.recall_at_5 - self.vector_only.recall_at_5

    @property
    def mrr_delta(self) -> float:
        return self.hybrid.mrr - self.vector_only.mrr

    @property
    def both_metrics_improved(self) -> bool:
        return self.recall_at_5_delta > 0 and self.mrr_delta > 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "vector_only": self.vector_only.as_dict(),
            "hybrid": self.hybrid.as_dict(),
            "recall_at_5_delta": self.recall_at_5_delta,
            "mrr_delta": self.mrr_delta,
            "both_metrics_improved": self.both_metrics_improved,
        }


SearchFunction = Callable[..., Sequence[HybridSearchResult]]


def _search_case(case: GoldenQuery, search: SearchFunction) -> Sequence[HybridSearchResult]:
    """Apply golden metadata filters while retaining compatibility with simple test doubles."""
    filters = {name: value for name, value in (("speaker", case.speaker), ("source", case.source), ("date", case.date)) if value is not None}
    try:
        return search(case.question, 5, **filters)
    except TypeError:
        return search(case.question, 5)


def evaluate_retrieval(cases: Sequence[GoldenQuery], search: SearchFunction) -> EvaluationSummary:
    """Run top-5 retrieval and calculate macro Recall@5 and MRR for relevant queries.

    Unanswerable cases have no relevant chunk identifiers, so Recall and MRR are
    mathematically undefined for them. They stay in ``per_query`` with null
    scores and are excluded from the aggregate denominators.
    """
    records: list[QueryMetrics] = []
    recalls: list[float] = []
    reciprocal_ranks: list[float] = []
    for case in cases:
        started_at = perf_counter()
        results = _search_case(case, search)
        retrieval_time_ms = (perf_counter() - started_at) * 1_000
        result_ids = tuple(result.chunk.id for result in results)
        if case.expected_chunk_ids:
            recall = recall_at_k(result_ids, case.expected_chunk_ids)
            rank = reciprocal_rank(result_ids, case.expected_chunk_ids)
            recalls.append(recall)
            reciprocal_ranks.append(rank)
        else:
            recall = None
            rank = None
        records.append(
            QueryMetrics(
                question_id=case.question_id,
                query_category=case.query_category,
                retrieved_chunk_ids=result_ids,
                retrieval_time_ms=retrieval_time_ms,
                generation_time_ms=None,
                top_chunk_rrf_scores=tuple(result.rrf_score for result in results),
                top_chunk_vector_similarity_scores=tuple(result.vector_score for result in results),
                recall_at_5=recall,
                reciprocal_rank=rank,
            )
        )
    relevant_queries = len(recalls)
    unanswerable_queries = len(cases) - relevant_queries
    return EvaluationSummary(
        total_queries=len(cases),
        relevant_queries=relevant_queries,
        unanswerable_queries=unanswerable_queries,
        recall_at_5=sum(recalls) / relevant_queries if relevant_queries else 0.0,
        mrr=sum(reciprocal_ranks) / relevant_queries if relevant_queries else 0.0,
        per_query=tuple(records),
    )


def compare_retrieval_modes(
    cases: Sequence[GoldenQuery],
    *,
    vector_search: SearchFunction,
    hybrid_search: SearchFunction,
) -> RetrievalComparison:
    """Evaluate vector-only and hybrid retrieval against the identical golden set."""
    return RetrievalComparison(
        vector_only=evaluate_retrieval(cases, vector_search),
        hybrid=evaluate_retrieval(cases, hybrid_search),
    )


def comparison_markdown(comparison: RetrievalComparison) -> str:
    """Render a compact before/after table suitable for a checked-in run report."""
    vector = comparison.vector_only
    hybrid = comparison.hybrid
    return "\n".join(
        (
            "| Retrieval mode | Recall@5 | MRR |",
            "| --- | ---: | ---: |",
            f"| Vector-only (before) | {vector.recall_at_5:.3f} | {vector.mrr:.3f} |",
            f"| Hybrid RRF (after) | {hybrid.recall_at_5:.3f} | {hybrid.mrr:.3f} |",
            (
                "| Change | "
                f"{comparison.recall_at_5_delta:+.3f} | {comparison.mrr_delta:+.3f} |"
            ),
        )
    )


@dataclass(frozen=True, slots=True)
class AnswerQueryMetrics:
    question_id: str
    query_category: str
    expected_abstention: bool
    abstained: bool
    answer_fact_coverage: float | None
    citation_valid: bool
    latency_ms: float


@dataclass(frozen=True, slots=True)
class AnswerEvaluationSummary:
    total_queries: int
    answerable_queries: int
    abstention_precision: float
    abstention_recall: float
    abstention_f1: float
    mean_answer_fact_coverage: float
    citation_validity_rate: float
    p50_latency_ms: float
    p95_latency_ms: float
    per_query: tuple[AnswerQueryMetrics, ...]

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["per_query"] = list(payload["per_query"])
        return payload


AnswerFunction = Callable[..., Any]


def _normalized(value: str) -> str:
    return "".join(character.casefold() for character in value if character.isalnum())


def evaluate_answers(cases: Sequence[GoldenQuery], answer: AnswerFunction) -> AnswerEvaluationSummary:
    """Score abstention, required-answer-fact coverage, citations, and latency."""
    records: list[AnswerQueryMetrics] = []
    true_positive = false_positive = false_negative = 0
    coverages: list[float] = []
    citation_checks: list[bool] = []
    latencies: list[float] = []
    for case in cases:
        filters = {name: value for name, value in (("speaker", case.speaker), ("source", case.source), ("date", case.date)) if value is not None}
        started_at = perf_counter()
        response = answer(case.question, **filters)
        latency = (perf_counter() - started_at) * 1_000
        latencies.append(latency)
        expected_abstention = not case.expected_chunks
        abstained = response.status == "no_relevant_information"
        if expected_abstention and abstained:
            true_positive += 1
        elif not expected_abstention and abstained:
            false_negative += 1
        elif expected_abstention:
            false_positive += 1
        if expected_abstention:
            coverage = None
            citation_valid = not response.citations
        else:
            facts = [_normalized(fact) for fact in case.required_answer_facts]
            answer_text = _normalized(response.answer)
            coverage = sum(fact in answer_text for fact in facts) / len(facts) if facts else 1.0
            citation_valid = response.status == "answered" and bool(response.citations)
            coverages.append(coverage)
        citation_checks.append(citation_valid)
        records.append(AnswerQueryMetrics(case.question_id, case.query_category, expected_abstention, abstained, coverage, citation_valid, latency))
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    ordered_latencies = sorted(latencies)

    def percentile(quantile: float) -> float:
        if not ordered_latencies:
            return 0.0
        index = min(len(ordered_latencies) - 1, int((len(ordered_latencies) - 1) * quantile))
        return ordered_latencies[index]

    return AnswerEvaluationSummary(
        total_queries=len(cases),
        answerable_queries=len(cases) - sum(record.expected_abstention for record in records),
        abstention_precision=precision,
        abstention_recall=recall,
        abstention_f1=f1,
        mean_answer_fact_coverage=sum(coverages) / len(coverages) if coverages else 0.0,
        citation_validity_rate=sum(citation_checks) / len(citation_checks) if citation_checks else 0.0,
        p50_latency_ms=percentile(0.50),
        p95_latency_ms=percentile(0.95),
        per_query=tuple(records),
    )
