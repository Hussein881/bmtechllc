"""Deterministic abstention-threshold selection over a reviewed golden set."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from typing import Any

from ..models import GoldenQuery
from ..retrieval import HybridSearchResult, meaningful_keyword_overlap


@dataclass(frozen=True, slots=True)
class AbstentionCalibration:
    min_cosine_similarity: float
    min_keyword_overlap: int
    answerable_acceptance_rate: float
    near_miss_false_accept_rate: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


SearchFunction = Callable[..., Sequence[HybridSearchResult]]


def calibrate_abstention(
    cases: Sequence[GoldenQuery],
    search: SearchFunction,
    *,
    cosine_candidates: Sequence[float] = tuple(value / 100 for value in range(20, 61, 5)),
    keyword_candidates: Sequence[int] = (1, 2),
    max_near_miss_false_accept_rate: float = 0.05,
) -> AbstentionCalibration:
    """Maximize answerable acceptance under a near-miss false-accept constraint."""
    observed: list[tuple[GoldenQuery, Sequence[HybridSearchResult], float | None, int]] = []
    for case in cases:
        filters = {
            name: value
            for name, value in (("speaker", case.speaker), ("source", case.source), ("date", case.date))
            if value is not None
        }
        results = search(case.question, 5, **filters)
        top_cosine = max((item.vector_score for item in results if item.vector_score is not None), default=None)
        observed.append((case, results, top_cosine, meaningful_keyword_overlap(case.question, results)))
    viable: list[AbstentionCalibration] = []
    for cosine in cosine_candidates:
        for overlap in keyword_candidates:
            accepted = [
                bool(results) and score is not None and score >= cosine and keywords >= overlap
                for _, results, score, keywords in observed
            ]
            answerable = [flag for (case, *_), flag in zip(observed, accepted, strict=True) if case.expected_chunks]
            near_misses = [flag for (case, *_), flag in zip(observed, accepted, strict=True) if not case.expected_chunks]
            answerable_rate = sum(answerable) / len(answerable) if answerable else 0.0
            false_accept_rate = sum(near_misses) / len(near_misses) if near_misses else 0.0
            if false_accept_rate <= max_near_miss_false_accept_rate:
                viable.append(AbstentionCalibration(cosine, overlap, answerable_rate, false_accept_rate))
    if not viable:
        raise ValueError("No cutoff pair meets the near-miss false-accept constraint.")
    return max(
        viable,
        key=lambda item: (
            item.answerable_acceptance_rate,
            item.min_cosine_similarity,
            item.min_keyword_overlap,
        ),
    )
