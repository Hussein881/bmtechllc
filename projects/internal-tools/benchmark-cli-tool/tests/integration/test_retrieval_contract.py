"""Offline contract tests for keyword/vector retrieval result compatibility."""

from __future__ import annotations

import os
import re
import unittest
from pathlib import Path

import pytest

from benchmark_cli import retrieval

FIXTURE_DIR = Path(__file__).parents[1] / "fixtures" / "documents"


@pytest.mark.integration
class SearchContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.old_mode = os.environ.get("SEARCH_MODE")
        self.original_vector = retrieval._vector_search
        self.original_documents_dir = retrieval.DOCUMENTS_DIR
        retrieval.DOCUMENTS_DIR = FIXTURE_DIR

    def tearDown(self) -> None:
        if self.old_mode is None:
            os.environ.pop("SEARCH_MODE", None)
        else:
            os.environ["SEARCH_MODE"] = self.old_mode
        retrieval._vector_search = self.original_vector
        retrieval.DOCUMENTS_DIR = self.original_documents_dir

    def _assert_shape(self, results: list[dict[str, str]]) -> None:
        self.assertTrue(results)
        self.assertEqual(set(results[0]), {"filename", "location", "snippet"})

    def _known_query(self) -> str:
        documents = retrieval.list_docs()
        self.assertTrue(documents, "The search contract requires one local document.")
        text = retrieval.read_doc(documents[0]["filename"])
        terms = re.findall(r"[A-Za-z]{4,}", text)
        self.assertTrue(terms, "The selected document did not contain a searchable word.")
        return terms[0]

    def test_keyword_mode_and_zero_hits(self) -> None:
        os.environ["SEARCH_MODE"] = "keyword"
        self._assert_shape(retrieval.search_docs(self._known_query()))
        self.assertEqual(retrieval.search_docs("unfindable-week-two-term"), [])
        self.assertEqual(retrieval.search_docs(""), [])

    def test_vector_mode_returns_the_identical_public_shape(self) -> None:
        os.environ["SEARCH_MODE"] = "vector"
        retrieval._vector_search = lambda query, limit: [
            {"filename": "source.txt", "location": "Policy", "snippet": f"hit for {query}"}
        ]
        self._assert_shape(retrieval.search_docs(self._known_query()))

    def test_unavailable_vector_backend_falls_back_cleanly(self) -> None:
        os.environ["SEARCH_MODE"] = "vector"

        def unavailable(_: str, __: int) -> list[dict[str, str]]:
            raise RuntimeError("database unavailable")

        retrieval._vector_search = unavailable
        self._assert_shape(retrieval.search_docs(self._known_query()))

    def test_transcript_source_stem_is_a_readable_full_document_alias(self) -> None:
        transcript = next(
            (doc for doc in retrieval.list_docs() if "transcript" in doc["filename"]),
            None,
        )
        self.assertIsNotNone(transcript, "The source library requires a transcript fixture.")
        assert transcript is not None
        self.assertEqual(
            retrieval.read_doc(transcript["filename"], Path(transcript["filename"]).stem),
            retrieval.read_doc(transcript["filename"]),
        )
        self.assertEqual(
            retrieval.read_doc(transcript["filename"], "full document (line 1)"),
            retrieval.read_doc(transcript["filename"]),
        )


if __name__ == "__main__":
    unittest.main()
