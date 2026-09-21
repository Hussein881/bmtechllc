"""Tests for provenance constraints applied to both retrieval arms."""

from __future__ import annotations

import pytest

from benchmark_cli import retrieval
from benchmark_cli.storage.postgres import SearchChunk, SearchFilters


def chunk(chunk_id: int) -> SearchChunk:
    return SearchChunk(chunk_id, "meeting.txt", 0, "text", {}, 1.0)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("name", "value"),
    (("speaker", "Ada"), ("source", "meeting.txt"), ("date", "2026-08-14")),
)
def test_search_docs_applies_each_optional_filter_to_keyword_and_vector(
    monkeypatch: pytest.MonkeyPatch, name: str, value: str
) -> None:
    calls: list[tuple[str, dict[str, str | None]]] = []
    monkeypatch.setattr(retrieval, "embed_texts", lambda _: [[0.1, 0.2]])

    def fake_vector(_: object, __: int, **filters: str | None) -> list[SearchChunk]:
        calls.append(("vector", filters))
        return [chunk(1)]

    def fake_fts(_: str, __: int, **filters: str | None) -> list[SearchChunk]:
        calls.append(("fts", filters))
        return [chunk(2)]

    monkeypatch.setattr(retrieval, "vector_search", fake_vector)
    monkeypatch.setattr(retrieval, "fts_search", fake_fts)

    retrieval.search_docs("filter test", **{name: value})

    assert {arm for arm, _ in calls} == {"vector", "fts"}
    assert all(filters[name] == value for _, filters in calls)


@pytest.mark.unit
def test_date_filter_requires_an_iso_date() -> None:
    with pytest.raises(ValueError, match="ISO-8601"):
        SearchFilters(date="August 14")
