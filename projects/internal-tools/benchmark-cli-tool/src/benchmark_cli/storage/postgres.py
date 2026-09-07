"""PostgreSQL persistence for chunk ingestion and independent retrieval modes."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config import (
    DATABASE_URL,
    DB_STATEMENT_TIMEOUT_MS,
    HNSW_EF_SEARCH,
    PARENT_CONTEXT_MAX_TOKENS,
)

SQL_DIR = Path(__file__).with_name("sql")


@dataclass(frozen=True, slots=True)
class SearchChunk:
    """A persisted chunk returned by one retrieval mode."""

    id: int
    source_file: str
    chunk_index: int
    chunk_text: str
    metadata: dict[str, Any]
    score: float
    token_count: int | None = None


@dataclass(frozen=True, slots=True)
class ParentContext:
    """A hit plus nearby chunks from its containing source section."""

    anchor: SearchChunk
    section: str | None
    chunks: tuple[SearchChunk, ...]
    token_count: int
    section_complete: bool


def _dependencies() -> tuple[Any, Any, Any]:
    try:
        import psycopg
        from pgvector.psycopg import register_vector
        from psycopg.types.json import Json
    except ImportError as exc:
        raise RuntimeError("PostgreSQL retrieval requires psycopg[binary] and pgvector.") from exc
    return psycopg, register_vector, Json


@contextmanager
def connection() -> Iterator[Any]:
    """Yield a configured pgvector connection."""
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured.")
    psycopg, register_vector, _ = _dependencies()
    with psycopg.connect(DATABASE_URL) as conn:
        try:
            register_vector(conn)
        except psycopg.ProgrammingError as exc:
            if "vector type not found" not in str(exc):
                raise
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT set_config('statement_timeout', %s, false)",
                (str(DB_STATEMENT_TIMEOUT_MS),),
            )
            cursor.execute("SELECT set_config('hnsw.ef_search', %s, false)", (str(HNSW_EF_SEARCH),))
        yield conn


def apply_sql(filename: str) -> None:
    """Apply one checked-in, idempotent SQL migration."""
    sql_path = SQL_DIR / filename
    if not sql_path.is_file():
        raise ValueError(f"Unknown SQL migration: {filename}")
    with connection() as conn, conn.cursor() as cursor:
        cursor.execute(sql_path.read_text(encoding="utf-8"))
        conn.commit()


def initialize_database() -> None:
    """Create or upgrade the chunk table, vector support, and FTS field."""
    apply_sql("001_init.sql")
    apply_sql("002_fts.sql")


def create_indexes() -> None:
    """Create vector, FTS, and supporting indexes after ingestion."""
    apply_sql("003_indexes.sql")


def existing_hashes(hashes: Sequence[str]) -> set[str]:
    if not hashes:
        return set()
    with connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            "SELECT content_sha256 FROM document_chunks WHERE content_sha256 = ANY(%s)",
            (list(hashes),),
        )
        return {row[0].strip() for row in cursor.fetchall()}


def delete_source(source_file: str) -> None:
    with connection() as conn, conn.cursor() as cursor:
        cursor.execute("DELETE FROM document_chunks WHERE source_file = %s", (source_file,))
        conn.commit()


def upsert_chunks(rows: Sequence[dict[str, Any]]) -> int:
    """Insert new chunks; the generated FTS column is derived by PostgreSQL."""
    if not rows:
        return 0
    _, _, Json = _dependencies()
    statement = """
        INSERT INTO document_chunks
            (source_file, chunk_index, chunk_text, content_sha256, token_count, embedding, metadata)
        VALUES (%(source_file)s, %(chunk_index)s, %(chunk_text)s, %(content_sha256)s,
                %(token_count)s, %(embedding)s, %(metadata)s)
        ON CONFLICT (content_sha256) DO NOTHING
    """
    prepared = [{**row, "metadata": Json(row["metadata"])} for row in rows]
    with connection() as conn, conn.cursor() as cursor:
        cursor.executemany(statement, prepared)
        inserted = cursor.rowcount
        conn.commit()
    return inserted


def vector_search(query_vector: Sequence[float], limit: int = 20) -> list[SearchChunk]:
    """Return vector-ranked candidates independently of keyword retrieval."""
    if limit < 1:
        return []
    statement = """
        SELECT id, source_file, chunk_index, chunk_text, metadata,
               1 - (embedding <=> %s::vector) AS score
        FROM document_chunks
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """
    with connection() as conn, conn.cursor() as cursor:
        cursor.execute(statement, (list(query_vector), list(query_vector), limit))
        return [SearchChunk(*row) for row in cursor.fetchall()]


def fts_search(query: str, limit: int = 20) -> list[SearchChunk]:
    """Return PostgreSQL full-text-ranked candidates independently of vectors."""
    if not query.strip() or limit < 1:
        return []
    statement = """
        SELECT id, source_file, chunk_index, chunk_text, metadata,
               ts_rank_cd(search_vector, websearch_to_tsquery('english', %s)) AS score
        FROM document_chunks
        WHERE search_vector @@ websearch_to_tsquery('english', %s)
        ORDER BY score DESC, id ASC
        LIMIT %s
    """
    with connection() as conn, conn.cursor() as cursor:
        cursor.execute(statement, (query, query, limit))
        return [SearchChunk(*row) for row in cursor.fetchall()]


def select_context_window(
    chunks: Sequence[SearchChunk], anchor_id: int, max_tokens: int
) -> tuple[tuple[SearchChunk, ...], int, bool]:
    """Return a contiguous, token-bounded window centered on an anchor chunk."""
    if max_tokens < 1:
        raise ValueError("max_tokens must be at least 1.")
    try:
        anchor_index = next(index for index, chunk in enumerate(chunks) if chunk.id == anchor_id)
    except StopIteration as exc:
        raise ValueError(f"Anchor chunk {anchor_id} is not present in the supplied section.") from exc

    included = {anchor_index}
    total = chunks[anchor_index].token_count
    if total is None or total < 1:
        raise ValueError("Context chunks must provide a positive token_count.")

    left = anchor_index - 1
    right = anchor_index + 1
    while left >= 0 or right < len(chunks):
        added = False
        for side in ("left", "right"):
            candidate_index = left if side == "left" else right
            if candidate_index < 0 or candidate_index >= len(chunks):
                continue
            candidate_tokens = chunks[candidate_index].token_count
            if candidate_tokens is None or candidate_tokens < 1:
                raise ValueError("Context chunks must provide a positive token_count.")
            if total + candidate_tokens > max_tokens:
                if side == "left":
                    left = -1
                else:
                    right = len(chunks)
                continue
            included.add(candidate_index)
            total += candidate_tokens
            added = True
            if side == "left":
                left -= 1
            else:
                right += 1
        if not added:
            break

    selected = tuple(chunk for index, chunk in enumerate(chunks) if index in included)
    return selected, total, len(selected) == len(chunks)


def read_doc(chunk_id: int, *, max_tokens: int = PARENT_CONTEXT_MAX_TOKENS) -> ParentContext | None:
    """Fetch the hit and a token-bounded window from its containing section.

    The containing section is defined by ``source_file`` plus the persisted
    ``metadata.section`` value. When the section exceeds ``max_tokens``, the
    returned chunks are the nearest siblings around the hit and
    ``section_complete`` is false.
    """
    if chunk_id < 1:
        raise ValueError("chunk_id must be at least 1.")
    if max_tokens < 1:
        raise ValueError("max_tokens must be at least 1.")
    anchor_statement = """
        SELECT id, source_file, chunk_index, chunk_text, metadata, 0.0 AS score,
               token_count
        FROM document_chunks
        WHERE id = %s
    """
    section_statement = """
        SELECT id, source_file, chunk_index, chunk_text, metadata, 0.0 AS score,
               token_count
        FROM document_chunks
        WHERE source_file = %s
          AND (metadata ->> 'section') IS NOT DISTINCT FROM %s
        ORDER BY chunk_index ASC, id ASC
    """
    with connection() as conn, conn.cursor() as cursor:
        cursor.execute(anchor_statement, (chunk_id,))
        anchor_row = cursor.fetchone()
        if anchor_row is None:
            return None
        anchor = SearchChunk(*anchor_row)
        section = anchor.metadata.get("section")
        if section is not None:
            section = str(section)
        cursor.execute(section_statement, (anchor.source_file, section))
        section_rows = cursor.fetchall()

    section_chunks = tuple(SearchChunk(*row) for row in section_rows)
    selected, total, complete = select_context_window(section_chunks, anchor.id, max_tokens)
    return ParentContext(anchor, section, selected, total, complete)
