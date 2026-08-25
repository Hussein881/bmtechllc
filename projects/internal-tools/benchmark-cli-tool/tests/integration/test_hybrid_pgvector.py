"""Opt-in end-to-end test using real OpenAI embeddings and local pgvector."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import pytest

from benchmark_cli.config import DATABASE_URL, OPENAI_API_KEY
from benchmark_cli.ingestion.pipeline import ingest_source
from benchmark_cli.providers.openai import embed_texts
from benchmark_cli.retrieval import hybrid_search
from benchmark_cli.storage.postgres import (
    connection,
    create_indexes,
    fts_search,
    initialize_database,
    vector_search,
)

pytestmark = pytest.mark.integration_live

FIXTURE_DIR = Path(__file__).parents[1] / "fixtures" / "integration"


def _is_local_compose_database() -> bool:
    """Only permit destructive test cleanup against the supplied local Compose DB."""
    if not DATABASE_URL:
        return False
    parsed = urlparse(DATABASE_URL)
    return parsed.hostname in {"localhost", "127.0.0.1"} and parsed.path.rstrip("/") == "/benchmark_cli"


def _truncate_chunks() -> None:
    with connection() as conn, conn.cursor() as cursor:
        cursor.execute("TRUNCATE document_chunks RESTART IDENTITY")
        conn.commit()


def test_ingestion_and_hybrid_search_with_pgvector_and_fts() -> None:
    """Index fixtures and verify vector, FTS, and fused results find the policy chunk."""
    if not OPENAI_API_KEY:
        pytest.skip("OPENAI_API_KEY is required for real embeddings.")
    if not _is_local_compose_database():
        pytest.skip("Test only runs against the local benchmark_cli Docker database.")

    initialize_database()
    _truncate_chunks()
    try:
        reports = [
            ingest_source(path, dry_run=False, force=True, batch_size=16)
            for path in sorted(FIXTURE_DIR.glob("*.txt"))
        ]
        create_indexes()
        assert sum(report["inserted"] for report in reports) >= 2

        query = "equipment reimbursement"
        fts_candidates = fts_search(query)
        vector_candidates = vector_search(embed_texts([query])[0])
        hybrid_candidates = hybrid_search(query)

        assert fts_candidates and "five hundred dollars" in fts_candidates[0].chunk_text
        assert vector_candidates and "five hundred dollars" in vector_candidates[0].chunk_text
        assert hybrid_candidates and "five hundred dollars" in hybrid_candidates[0].chunk.chunk_text
    finally:
        _truncate_chunks()
