"""Persistent, CSV-based telemetry for OpenAI model usage."""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path

from ..config import ModelConfig, get_model_config
from ..paths import artifact_path

USAGE_LOG_PATH = artifact_path("telemetry", "usage_log.csv")
CSV_FIELDS = (
    "timestamp",
    "component",
    "question",
    "tier",
    "model",
    "prompt_tokens",
    "completion_tokens",
    "total_cost_usd",
    "flagship_equivalent_cost_usd",
    "routing_savings_usd",
)


def calculate_cost_usd(
    model_config: ModelConfig, prompt_tokens: int, completion_tokens: int
) -> float:
    """Calculate a request's cost from its input and output token counts."""
    return (
        prompt_tokens * model_config.input_cost_per_million
        + completion_tokens * model_config.output_cost_per_million
    ) / 1_000_000


def _routing_costs(
    *,
    model: str,
    component: str,
    prompt_tokens: int,
    completion_tokens: int,
    actual_cost: float,
) -> tuple[float, float]:
    """Return the Terra-equivalent cost and savings for a routed agent call."""
    cheap_model = get_model_config("cheap").model
    if component != "agent" or model != cheap_model:
        return actual_cost, 0.0
    flagship_cost = calculate_cost_usd(
        get_model_config("flagship"), prompt_tokens, completion_tokens
    )
    return flagship_cost, max(flagship_cost - actual_cost, 0.0)


def _format_cost(value: float) -> str:
    """Format a USD value consistently for CSV telemetry."""
    return f"{value:.10f}"


def _backfill_routing_costs(row: dict[str, str]) -> dict[str, str]:
    """Preserve an existing row while adding comparable routing-cost fields."""
    normalized = {field: row.get(field, "") for field in CSV_FIELDS}
    try:
        prompt_tokens = int(normalized["prompt_tokens"])
        completion_tokens = int(normalized["completion_tokens"])
        actual_cost = float(normalized["total_cost_usd"])
    except (TypeError, ValueError):
        normalized["flagship_equivalent_cost_usd"] = normalized["total_cost_usd"]
        normalized["routing_savings_usd"] = "0.0000000000"
        return normalized
    equivalent_cost, savings = _routing_costs(
        model=normalized["model"],
        component=normalized["component"],
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        actual_cost=actual_cost,
    )
    normalized["flagship_equivalent_cost_usd"] = _format_cost(equivalent_cost)
    normalized["routing_savings_usd"] = _format_cost(savings)
    return normalized


def migrate_usage_log(log_path: Path = USAGE_LOG_PATH) -> None:
    """Add routing-savings columns to an existing telemetry file safely."""
    if not log_path.exists() or log_path.stat().st_size == 0:
        return
    with log_path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if tuple(reader.fieldnames or ()) == CSV_FIELDS:
            return
        rows = [_backfill_routing_costs(row) for row in reader]
    temporary_path = log_path.with_name(f"{log_path.name}.tmp")
    try:
        with temporary_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        temporary_path.replace(log_path)
    except OSError as exc:
        temporary_path.unlink(missing_ok=True)
        raise RuntimeError(f"Could not migrate usage log at {log_path}: {exc}") from exc


def log_usage(
    *,
    question: str,
    tier: str,
    model_config: ModelConfig,
    prompt_tokens: int,
    completion_tokens: int,
    component: str = "agent",
    log_path: Path = USAGE_LOG_PATH,
) -> None:
    """Append one model call's usage and calculated USD cost to a CSV file."""
    if prompt_tokens < 0 or completion_tokens < 0:
        raise ValueError("Token counts cannot be negative.")

    migrate_usage_log(log_path)
    should_write_header = not log_path.exists() or log_path.stat().st_size == 0
    actual_cost = calculate_cost_usd(model_config, prompt_tokens, completion_tokens)
    equivalent_cost, savings = _routing_costs(
        model=model_config.model,
        component=component,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        actual_cost=actual_cost,
    )
    row = {
        "timestamp": datetime.now(UTC).isoformat(),
        "component": component,
        "question": question,
        "tier": tier,
        "model": model_config.model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_cost_usd": _format_cost(actual_cost),
        "flagship_equivalent_cost_usd": _format_cost(equivalent_cost),
        "routing_savings_usd": _format_cost(savings),
    }

    try:
        with log_path.open("a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
            if should_write_header:
                writer.writeheader()
            writer.writerow(row)
    except OSError as exc:
        raise RuntimeError(f"Could not write usage log at {log_path}: {exc}") from exc
