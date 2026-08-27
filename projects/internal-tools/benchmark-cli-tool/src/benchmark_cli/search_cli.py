"""Inspect hybrid, full-text, or vector retrieval results from the command line."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from typing import Any

from .providers.openai import embed_texts
from .retrieval import HybridSearchResult, hybrid_search
from .storage.postgres import SearchChunk, fts_search, vector_search


def _chunk_payload(chunk: SearchChunk, rank: int, score: float, score_name: str) -> dict[str, Any]:
    return {
        "rank": rank,
        "chunk_id": chunk.id,
        "source_file": chunk.source_file,
        "chunk_index": chunk.chunk_index,
        score_name: score,
        "text": chunk.chunk_text,
        "metadata": chunk.metadata,
    }


def _hybrid_payload(results: Sequence[HybridSearchResult]) -> list[dict[str, Any]]:
    return [
        _chunk_payload(result.chunk, rank, result.rrf_score, "rrf_score")
        for rank, result in enumerate(results, start=1)
    ]


def _native_payload(results: Sequence[SearchChunk], score_name: str) -> list[dict[str, Any]]:
    return [
        _chunk_payload(result, rank, result.score, score_name)
        for rank, result in enumerate(results, start=1)
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True, help="Text to retrieve relevant chunks for.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results to return (default: 5).")
    parser.add_argument(
        "--mode",
        choices=("hybrid", "fts", "vector"),
        default="hybrid",
        help="Retrieval mode to inspect (default: hybrid).",
    )
    args = parser.parse_args()
    if args.top_k < 1:
        parser.error("--top-k must be at least 1")

    if args.mode == "hybrid":
        payload = _hybrid_payload(hybrid_search(args.query, args.top_k))
    elif args.mode == "fts":
        payload = _native_payload(fts_search(args.query, args.top_k), "fts_score")
    else:
        payload = _native_payload(
            vector_search(embed_texts([args.query])[0], args.top_k), "vector_score"
        )
    print(json.dumps({"mode": args.mode, "query": args.query, "results": payload}, indent=2))


if __name__ == "__main__":
    main()
