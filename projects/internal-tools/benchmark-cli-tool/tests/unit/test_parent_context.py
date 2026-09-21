"""Offline tests for parent-section context selection."""

from __future__ import annotations

from contextlib import contextmanager

import pytest

from benchmark_cli.storage import postgres
from benchmark_cli.storage.postgres import SearchChunk, select_context_window


def chunk(identifier: int, index: int, tokens: int = 20) -> SearchChunk:
    return SearchChunk(
        id=identifier,
        source_file="handbook.md",
        chunk_index=index,
        chunk_text=f"chunk {identifier}",
        metadata={"section": "Benefits"},
        score=0.0,
        token_count=tokens,
    )


@pytest.mark.unit
def test_context_window_returns_contiguous_siblings_around_hit() -> None:
    chunks = tuple(chunk(identifier, identifier - 1) for identifier in range(1, 5))

    selected, total, complete = select_context_window(chunks, anchor_id=2, max_tokens=60)

    assert [item.id for item in selected] == [1, 2, 3]
    assert total == 60
    assert not complete


@pytest.mark.unit
def test_context_window_marks_complete_section() -> None:
    chunks = tuple(chunk(identifier, identifier - 1) for identifier in range(1, 4))

    selected, total, complete = select_context_window(chunks, anchor_id=2, max_tokens=100)

    assert [item.id for item in selected] == [1, 2, 3]
    assert total == 60
    assert complete


@pytest.mark.unit
def test_read_doc_fetches_siblings_from_the_hit_section(monkeypatch: pytest.MonkeyPatch) -> None:
    anchor_row = (2, "handbook.md", 1, "chunk 2", {"section": "Benefits"}, 0.0, 20)
    section_rows = [
        (1, "handbook.md", 0, "chunk 1", {"section": "Benefits"}, 0.0, 20),
        anchor_row,
        (3, "handbook.md", 2, "chunk 3", {"section": "Benefits"}, 0.0, 20),
    ]

    class FakeCursor:
        def __init__(self) -> None:
            self.calls: list[tuple[str, tuple[object, ...]]] = []

        def __enter__(self) -> FakeCursor:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def execute(self, statement: str, parameters: tuple[object, ...]) -> None:
            self.calls.append((statement, parameters))

        def fetchone(self) -> tuple[object, ...]:
            return anchor_row

        def fetchall(self) -> list[tuple[object, ...]]:
            return section_rows

    cursor = FakeCursor()

    class FakeConnection:
        def cursor(self) -> FakeCursor:
            return cursor

    @contextmanager
    def fake_connection():
        yield FakeConnection()

    monkeypatch.setattr(postgres, "connection", fake_connection)

    context = postgres.read_doc(2, max_tokens=60)

    assert context is not None
    assert [item.id for item in context.chunks] == [1, 2, 3]
    assert context.section == "Benefits"
    assert context.section_complete
    assert cursor.calls[0][1] == (2,)
    assert cursor.calls[1][1] == ("handbook.md", "Benefits")
