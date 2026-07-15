"""SQLite manifest for incremental ingestion identity tracking."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable


@dataclass(frozen=True)
class ManifestEntry:
    file_path: str
    content_hash: str
    size_bytes: int
    mtime: float
    last_ingested_at: str
    loader_version: str
    chunker_version: str
    extractor_version: str
    chunk_count: int
    status: str
    error_detail: str


class IngestionManifest:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS manifest (
                    file_path TEXT PRIMARY KEY,
                    content_hash TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    mtime REAL NOT NULL,
                    last_ingested_at TEXT NOT NULL,
                    loader_version TEXT NOT NULL,
                    chunker_version TEXT NOT NULL,
                    extractor_version TEXT NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    error_detail TEXT NOT NULL
                )
                """
            )

    def fetch_all(self) -> Dict[str, ManifestEntry]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM manifest").fetchall()
        return {row["file_path"]: self._to_entry(row) for row in rows}

    def upsert(self, entry: ManifestEntry) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO manifest (
                    file_path, content_hash, size_bytes, mtime, last_ingested_at,
                    loader_version, chunker_version, extractor_version,
                    chunk_count, status, error_detail
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(file_path) DO UPDATE SET
                    content_hash=excluded.content_hash,
                    size_bytes=excluded.size_bytes,
                    mtime=excluded.mtime,
                    last_ingested_at=excluded.last_ingested_at,
                    loader_version=excluded.loader_version,
                    chunker_version=excluded.chunker_version,
                    extractor_version=excluded.extractor_version,
                    chunk_count=excluded.chunk_count,
                    status=excluded.status,
                    error_detail=excluded.error_detail
                """,
                (
                    entry.file_path,
                    entry.content_hash,
                    entry.size_bytes,
                    entry.mtime,
                    entry.last_ingested_at,
                    entry.loader_version,
                    entry.chunker_version,
                    entry.extractor_version,
                    entry.chunk_count,
                    entry.status,
                    entry.error_detail,
                ),
            )

    def mark_deleted_missing(self, existing_paths: Iterable[str]) -> None:
        keep = set(existing_paths)
        with self._connect() as conn:
            rows = conn.execute("SELECT file_path FROM manifest WHERE status != 'deleted'").fetchall()
            for row in rows:
                path = row["file_path"]
                if path not in keep:
                    conn.execute(
                        "UPDATE manifest SET status='deleted', error_detail='' WHERE file_path=?",
                        (path,),
                    )

    def _to_entry(self, row: sqlite3.Row) -> ManifestEntry:
        return ManifestEntry(
            file_path=row["file_path"],
            content_hash=row["content_hash"],
            size_bytes=int(row["size_bytes"]),
            mtime=float(row["mtime"]),
            last_ingested_at=row["last_ingested_at"],
            loader_version=row["loader_version"],
            chunker_version=row["chunker_version"],
            extractor_version=row["extractor_version"],
            chunk_count=int(row["chunk_count"]),
            status=row["status"],
            error_detail=row["error_detail"],
        )
