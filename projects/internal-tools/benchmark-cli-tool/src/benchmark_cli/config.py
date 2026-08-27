"""Configuration for ingestion and hybrid retrieval."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

from dotenv import load_dotenv

from .paths import PROJECT_ROOT

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / ".env.local", override=False)

OPENAI_API_KEY: Final[str | None] = os.getenv("OPENAI_API_KEY")
DATABASE_URL: Final[str | None] = os.getenv("DATABASE_URL")
DB_STATEMENT_TIMEOUT_MS: Final[int] = int(os.getenv("DB_STATEMENT_TIMEOUT_MS", "5000"))
HNSW_EF_SEARCH: Final[int] = int(os.getenv("HNSW_EF_SEARCH", "40"))

EMBEDDING_MODEL: Final[str] = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSIONS: Final[int] = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
EMBEDDING_ENCODING: Final[str] = os.getenv("EMBEDDING_ENCODING", "cl100k_base")

CHUNK_TARGET_TOKENS: Final[int] = 400
CHUNK_MAX_TOKENS: Final[int] = 500
CHUNK_MIN_TOKENS: Final[int] = 80
CHUNK_OVERLAP_TOKENS: Final[int] = 50

DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
GOLDEN_DATASET_PATH: Final[Path] = DATA_DIR / "evaluation" / "golden_queries.example.json"
