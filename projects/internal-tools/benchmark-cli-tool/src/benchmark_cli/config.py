"""Central configuration for model selection and pricing."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from dotenv import load_dotenv

from .paths import PROJECT_ROOT

load_dotenv(PROJECT_ROOT / ".env")
# Keep developer-specific database endpoints out of the API-key file. Values
# here fill missing `.env` variables and are never committed.
load_dotenv(PROJECT_ROOT / ".env.local", override=False)

OPENAI_API_KEY: Final[str | None] = os.getenv("OPENAI_API_KEY")


@dataclass(frozen=True, slots=True)
class ModelConfig:
    """The API model identifier and per-token pricing for a model tier."""

    model: str
    input_cost_per_million: float
    output_cost_per_million: float


MODEL_TIERS: Final[Mapping[str, ModelConfig]] = {
    "cheap": ModelConfig(
        model="gpt-5.6-luna",
        input_cost_per_million=0.20,
        output_cost_per_million=1.20,
    ),
    "flagship": ModelConfig(
        model="gpt-5.6-terra",
        input_cost_per_million=2.00,
        output_cost_per_million=12.00,
    ),
    "embedding": ModelConfig(
        model="text-embedding-3-small",
        input_cost_per_million=0.02,
        output_cost_per_million=0.00,
    ),
}

EMBEDDING_TIER: Final[str] = "embedding"
EMBEDDING_DIMENSIONS: Final[int] = 1536
EMBEDDING_ENCODING: Final[str] = "cl100k_base"

CHUNK_TARGET_TOKENS: Final[int] = 400
CHUNK_MAX_TOKENS: Final[int] = 500
CHUNK_MIN_TOKENS: Final[int] = 80
CHUNK_OVERLAP_TOKENS: Final[int] = 50

SEARCH_MODE: Final[str] = os.getenv("SEARCH_MODE", "vector")
SEARCH_MIN_SIMILARITY: Final[float] = float(os.getenv("SEARCH_MIN_SIMILARITY", "0.25"))
SEARCH_OVERFETCH_FACTOR: Final[int] = int(os.getenv("SEARCH_OVERFETCH_FACTOR", "3"))
SEARCH_FALLBACK_KEYWORD: Final[bool] = (
    os.getenv("SEARCH_FALLBACK_KEYWORD", "true").strip().casefold() in {"1", "true", "yes"}
)

DATABASE_URL: Final[str | None] = os.getenv("DATABASE_URL")
DB_STATEMENT_TIMEOUT_MS: Final[int] = int(os.getenv("DB_STATEMENT_TIMEOUT_MS", "5000"))
HNSW_EF_SEARCH: Final[int] = int(os.getenv("HNSW_EF_SEARCH", "40"))


def get_model_config(tier: str) -> ModelConfig:
    """Return configuration for *tier*, rejecting unsupported model tiers."""
    try:
        return MODEL_TIERS[tier]
    except KeyError as exc:
        valid_tiers = ", ".join(MODEL_TIERS)
        raise ValueError(f"Unknown model tier {tier!r}. Expected one of: {valid_tiers}.") from exc
