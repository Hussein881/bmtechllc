"""Central configuration for model selection and pricing."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Final, Mapping

from dotenv import load_dotenv

load_dotenv()

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
        input_cost_per_million=1.00,
        output_cost_per_million=6.00,
    ),
    "flagship": ModelConfig(
        model="gpt-5.6-sol",
        input_cost_per_million=5.00,
        output_cost_per_million=30.00,
    ),
}


def get_model_config(tier: str) -> ModelConfig:
    """Return configuration for *tier*, rejecting unsupported model tiers."""
    try:
        return MODEL_TIERS[tier]
    except KeyError as exc:
        valid_tiers = ", ".join(MODEL_TIERS)
        raise ValueError(f"Unknown model tier {tier!r}. Expected one of: {valid_tiers}.") from exc
