"""Hybrid vector and full-text chunk retrieval using Reciprocal Rank Fusion."""

from __future__ import annotations

from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace

from .providers.openai import embed_texts
from .storage.postgres import SearchChunk, SearchFilters, fts_search, vector_search

CANDIDATE_LIMIT = 20
RRF_K = 60


@dataclass(frozen=True, slots=True)
class HybridSearchResult:
    """A deduplicated chunk annotated with its fused rank score."""

    chunk: SearchChunk
    rrf_score: float
    vector_score: float | None = None
    fts_score: float | None = None


def rrf_fuse(
    ranked_lists: Sequence[Sequence[SearchChunk]], *, rrf_k: int = RRF_K
) -> list[HybridSearchResult]:
    """Merge ranked lists with 1-based Reciprocal Rank Fusion scoring."""
    if rrf_k < 0:
        raise ValueError("rrf_k must be non-negative.")
    scores: dict[int, float] = {}
    chunks: dict[int, SearchChunk] = {}
    for ranked_list in ranked_lists:
        for rank, chunk in enumerate(ranked_list, start=1):
            chunks.setdefault(chunk.id, chunk)
            scores[chunk.id] = scores.get(chunk.id, 0.0) + 1.0 / (rrf_k + rank)
    return sorted(
        (HybridSearchResult(chunks[chunk_id], score) for chunk_id, score in scores.items()),
        key=lambda result: (-result.rrf_score, result.chunk.id),
    )


def search_docs(
    query: str,
    top_k: int = 5,
    *,
    speaker: str | None = None,
    source: str | None = None,
    date: str | None = None,
) -> list[HybridSearchResult]:
    """Run filtered 20-per-arm keyword/vector retrieval and return RRF top results."""
    if not query.strip():
        return []
    if top_k < 1:
        return []
    filters = SearchFilters(speaker=speaker, source=source, date=date)
    query_embedding = embed_texts([query])[0]
    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="hybrid-search") as executor:
        vector_future = executor.submit(
            vector_search,
            query_embedding,
            CANDIDATE_LIMIT,
            speaker=filters.speaker,
            source=filters.source,
            date=filters.date,
        )
        fts_future = executor.submit(
            fts_search,
            query,
            CANDIDATE_LIMIT,
            speaker=filters.speaker,
            source=filters.source,
            date=filters.date,
        )
        vector_candidates = vector_future.result()
        fts_candidates = fts_future.result()
    vector_scores = {chunk.id: chunk.score for chunk in vector_candidates}
    fts_scores = {chunk.id: chunk.score for chunk in fts_candidates}
    return [
        replace(
            result,
            vector_score=vector_scores.get(result.chunk.id),
            fts_score=fts_scores.get(result.chunk.id),
        )
        for result in rrf_fuse((vector_candidates, fts_candidates))[:top_k]
    ]


def hybrid_search(
    query: str,
    top_k: int = 5,
    *,
    speaker: str | None = None,
    source: str | None = None,
    date: str | None = None,
) -> list[HybridSearchResult]:
    """Backward-compatible name for :func:`search_docs`."""
    return search_docs(query, top_k, speaker=speaker, source=source, date=date)


def vector_only_search(
    query: str,
    top_k: int = 5,
    *,
    speaker: str | None = None,
    source: str | None = None,
    date: str | None = None,
) -> list[HybridSearchResult]:
    """Return vector-only results in the common evaluation result shape."""
    if not query.strip() or top_k < 1:
        return []
    filters = SearchFilters(speaker=speaker, source=source, date=date)
    candidates = vector_search(
        embed_texts([query])[0],
        top_k,
        speaker=filters.speaker,
        source=filters.source,
        date=filters.date,
    )
    return [
        HybridSearchResult(chunk, rrf_score=0.0, vector_score=chunk.score)
        for chunk in candidates
    ]
