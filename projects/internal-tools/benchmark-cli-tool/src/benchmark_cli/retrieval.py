"""Hybrid vector and full-text chunk retrieval using Reciprocal Rank Fusion."""

from __future__ import annotations

from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from .providers.openai import embed_texts
from .storage.postgres import SearchChunk, fts_search, vector_search

CANDIDATE_LIMIT = 20
RRF_K = 60


@dataclass(frozen=True, slots=True)
class HybridSearchResult:
    """A deduplicated chunk annotated with its fused rank score."""

    chunk: SearchChunk
    rrf_score: float


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


def hybrid_search(query: str, top_k: int = 5) -> list[HybridSearchResult]:
    """Retrieve 20 vector and 20 FTS candidates concurrently, then RRF-rerank them."""
    if not query.strip():
        return []
    if top_k < 1:
        return []
    query_embedding = embed_texts([query])[0]
    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="hybrid-search") as executor:
        vector_future = executor.submit(vector_search, query_embedding, CANDIDATE_LIMIT)
        fts_future = executor.submit(fts_search, query, CANDIDATE_LIMIT)
        vector_candidates = vector_future.result()
        fts_candidates = fts_future.result()
    return rrf_fuse((vector_candidates, fts_candidates))[:top_k]
