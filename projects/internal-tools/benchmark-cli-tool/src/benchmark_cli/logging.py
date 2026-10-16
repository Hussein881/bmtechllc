"""Append-only usage telemetry with routed-versus-flagship cost accounting."""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path

from .config import ModelConfig, get_model_config
from .paths import PROJECT_ROOT

USAGE_LOG_PATH = PROJECT_ROOT / "artifacts" / "model_usage.csv"
AGENT_DIAGNOSTIC_LOG_PATH = PROJECT_ROOT / "artifacts" / "agent_diagnostics.csv"
CSV_FIELDS = (
    "timestamp_utc",
    "component",
    "tier",
    "model",
    "prompt_tokens",
    "completion_tokens",
    "latency_ms",
    "actual_cost_usd",
    "flagship_equivalent_cost_usd",
    "routing_savings_usd",
)
AGENT_DIAGNOSTIC_FIELDS = ("timestamp_utc", "outcome", "synthesis_attempts")


def calculate_cost_usd(model: ModelConfig, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate USD cost from published per-million-token prices."""
    return (
        prompt_tokens * model.input_cost_per_million + completion_tokens * model.output_cost_per_million
    ) / 1_000_000


def log_usage(
    *,
    tier: str,
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: float,
    component: str,
    log_path: Path = USAGE_LOG_PATH,
) -> None:
    """Persist one model call without storing user or document content."""
    if prompt_tokens < 0 or completion_tokens < 0 or latency_ms < 0:
        raise ValueError("Token counts and latency must not be negative.")
    model = get_model_config(tier)
    actual = calculate_cost_usd(model, prompt_tokens, completion_tokens)
    flagship = calculate_cost_usd(
        get_model_config("flagship"), prompt_tokens, completion_tokens
    )
    equivalent = flagship if tier == "cheap" and component != "embedding" else actual
    log_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not log_path.exists() or log_path.stat().st_size == 0
    with log_path.open("a", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp_utc": datetime.now(UTC).isoformat(),
                "component": component,
                "tier": tier,
                "model": model.model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "latency_ms": f"{latency_ms:.3f}",
                "actual_cost_usd": f"{actual:.10f}",
                "flagship_equivalent_cost_usd": f"{equivalent:.10f}",
                "routing_savings_usd": f"{max(equivalent - actual, 0.0):.10f}",
            }
        )


def log_agent_diagnostic(
    *, outcome: str, synthesis_attempts: int, log_path: Path = AGENT_DIAGNOSTIC_LOG_PATH
) -> None:
    """Persist a non-content answer-agent outcome for operational diagnosis."""
    if not outcome or synthesis_attempts < 0:
        raise ValueError("outcome must be non-empty and synthesis_attempts must be non-negative.")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not log_path.exists() or log_path.stat().st_size == 0
    with log_path.open("a", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=AGENT_DIAGNOSTIC_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp_utc": datetime.now(UTC).isoformat(),
                "outcome": outcome,
                "synthesis_attempts": synthesis_attempts,
            }
        )
