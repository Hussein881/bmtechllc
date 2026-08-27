"""Embedding-provider boundary used by ingestion and semantic retrieval."""

from __future__ import annotations

from collections.abc import Sequence

from openai import OpenAI

from ..config import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL, OPENAI_API_KEY

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """Construct the OpenAI client only when embeddings are requested."""
    global _client
    if _client is None:
        if not OPENAI_API_KEY or OPENAI_API_KEY == "your_openai_api_key_here":
            raise RuntimeError("OPENAI_API_KEY is not configured.")
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    """Embed non-empty texts and validate the configured vector dimension."""
    if not texts:
        return []
    if any(not text.strip() for text in texts):
        raise ValueError("texts must not contain empty values.")
    response = _get_client().embeddings.create(model=EMBEDDING_MODEL, input=list(texts))
    vectors = [item.embedding for item in response.data]
    if len(vectors) != len(texts):
        raise RuntimeError("Embedding response length did not match the input length.")
    if vectors and len(vectors[0]) != EMBEDDING_DIMENSIONS:
        raise RuntimeError(
            f"Embedding dimension mismatch: expected {EMBEDDING_DIMENSIONS}, got {len(vectors[0])}."
        )
    return vectors
