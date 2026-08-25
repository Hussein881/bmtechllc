"""Offline contract tests for the shared embeddings gateway."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

import pytest

from benchmark_cli.config import EMBEDDING_DIMENSIONS, EMBEDDING_TIER
from benchmark_cli.providers import openai as llm


@pytest.mark.unit
class EmbeddingGatewayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_client = llm._client
        self.original_log_usage = llm.log_usage
        self.logged: list[dict[str, object]] = []
        llm.log_usage = lambda **kwargs: self.logged.append(kwargs)  # type: ignore[assignment]

    def tearDown(self) -> None:
        llm._client = self.original_client
        llm.log_usage = self.original_log_usage  # type: ignore[assignment]

    def test_routes_to_embedding_tier_and_logs_usage(self) -> None:
        calls: list[dict[str, object]] = []

        class FakeEmbeddings:
            def create(self, **kwargs: object) -> object:
                calls.append(kwargs)
                return SimpleNamespace(
                    data=[SimpleNamespace(embedding=[0.1] * EMBEDDING_DIMENSIONS) for _ in kwargs["input"]],
                    usage=SimpleNamespace(prompt_tokens=12),
                )

        llm._client = SimpleNamespace(embeddings=FakeEmbeddings())
        vectors = llm.embed_texts(["one", "two"], component="query_embed")

        self.assertEqual(len(vectors), 2)
        self.assertEqual(calls[0]["model"], llm.get_model_config(EMBEDDING_TIER).model)
        self.assertEqual(self.logged[0]["component"], "query_embed")
        self.assertEqual(self.logged[0]["tier"], EMBEDDING_TIER)
        self.assertEqual(self.logged[0]["prompt_tokens"], 12)

    def test_rejects_wrong_embedding_dimension(self) -> None:
        class FakeEmbeddings:
            def create(self, **_: object) -> object:
                return SimpleNamespace(
                    data=[SimpleNamespace(embedding=[0.1, 0.2])],
                    usage=SimpleNamespace(prompt_tokens=1),
                )

        llm._client = SimpleNamespace(embeddings=FakeEmbeddings())
        with self.assertRaisesRegex(RuntimeError, "dimension mismatch"):
            llm.embed_texts(["one"])


if __name__ == "__main__":
    unittest.main()
