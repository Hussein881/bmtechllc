"""Metrics for evaluating retrieval results without answer generation."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
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


SearchFunction = Callable[[str, int], Sequence[HybridSearchResult]]


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
        result_ids = tuple(result.chunk.id for result in search(case.question, 5))
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
