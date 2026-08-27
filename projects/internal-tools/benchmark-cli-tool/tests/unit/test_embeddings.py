"""Offline contract tests for the embedding-provider boundary."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from benchmark_cli.config import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL
from benchmark_cli.providers import openai


@pytest.mark.unit
def test_embed_texts_uses_configured_model_and_preserves_input_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    class FakeEmbeddings:
        def create(self, **kwargs: object) -> object:
            calls.append(kwargs)
            return SimpleNamespace(
                data=[SimpleNamespace(embedding=[0.1] * EMBEDDING_DIMENSIONS) for _ in kwargs["input"]]
            )

    monkeypatch.setattr(openai, "_client", SimpleNamespace(embeddings=FakeEmbeddings()))
    vectors = openai.embed_texts(["one", "two"])

    assert len(vectors) == 2
    assert calls[0]["model"] == EMBEDDING_MODEL


@pytest.mark.unit
def test_embed_texts_rejects_wrong_embedding_dimension(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeEmbeddings:
        def create(self, **_: object) -> object:
            return SimpleNamespace(data=[SimpleNamespace(embedding=[0.1, 0.2])])

    monkeypatch.setattr(openai, "_client", SimpleNamespace(embeddings=FakeEmbeddings()))
    with pytest.raises(RuntimeError, match="dimension mismatch"):
        openai.embed_texts(["one"])
