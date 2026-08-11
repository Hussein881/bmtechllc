"""Offline contract tests for keyword/vector retrieval result compatibility."""

from __future__ import annotations

import os
import unittest

import tools


class SearchContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.old_mode = os.environ.get("SEARCH_MODE")
        self.original_vector = tools._vector_search

    def tearDown(self) -> None:
        if self.old_mode is None:
            os.environ.pop("SEARCH_MODE", None)
        else:
            os.environ["SEARCH_MODE"] = self.old_mode
        tools._vector_search = self.original_vector

    def _assert_shape(self, results: list[dict[str, str]]) -> None:
        self.assertTrue(results)
        self.assertEqual(set(results[0]), {"filename", "location", "snippet"})

    def test_keyword_mode_and_zero_hits(self) -> None:
        os.environ["SEARCH_MODE"] = "keyword"
        self._assert_shape(tools.search_docs("core hours"))
        self.assertEqual(tools.search_docs("unfindable-week-two-term"), [])
        self.assertEqual(tools.search_docs(""), [])

    def test_vector_mode_returns_the_identical_public_shape(self) -> None:
        os.environ["SEARCH_MODE"] = "vector"
        tools._vector_search = lambda query, limit: [
            {"filename": "source.txt", "location": "Policy", "snippet": f"hit for {query}"}
        ]
        self._assert_shape(tools.search_docs("core hours"))

    def test_unavailable_vector_backend_falls_back_cleanly(self) -> None:
        os.environ["SEARCH_MODE"] = "vector"

        def unavailable(_: str, __: int) -> list[dict[str, str]]:
            raise RuntimeError("database unavailable")

        tools._vector_search = unavailable
        self._assert_shape(tools.search_docs("core hours"))


if __name__ == "__main__":
    unittest.main()
