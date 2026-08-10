"""Persistent, CSV-based telemetry for OpenAI model usage."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

from config import ModelConfig

USAGE_LOG_PATH = Path(__file__).with_name("usage_log.csv")
CSV_FIELDS = (
    "timestamp",
    "question",
    "tier",
    "model",
    "prompt_tokens",
    "completion_tokens",
    "total_cost_usd",
)


def calculate_cost_usd(
    model_config: ModelConfig, prompt_tokens: int, completion_tokens: int
) -> float:
    """Calculate a request's cost from its input and output token counts."""
    return (
        prompt_tokens * model_config.input_cost_per_million
        + completion_tokens * model_config.output_cost_per_million
    ) / 1_000_000


def log_usage(
    *,
    question: str,
    tier: str,
    model_config: ModelConfig,
    prompt_tokens: int,
    completion_tokens: int,
    log_path: Path = USAGE_LOG_PATH,
) -> None:
    """Append one model call's usage and calculated USD cost to a CSV file."""
    if prompt_tokens < 0 or completion_tokens < 0:
        raise ValueError("Token counts cannot be negative.")

    should_write_header = not log_path.exists() or log_path.stat().st_size == 0
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "tier": tier,
        "model": model_config.model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_cost_usd": f"{calculate_cost_usd(model_config, prompt_tokens, completion_tokens):.10f}",
    }

    try:
        with log_path.open("a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
            if should_write_header:
                writer.writeheader()
            writer.writerow(row)
    except OSError as exc:
        raise RuntimeError(f"Could not write usage log at {log_path}: {exc}") from exc
