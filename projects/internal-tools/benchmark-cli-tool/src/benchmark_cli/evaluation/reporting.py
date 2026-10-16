"""Cost aggregation for answer evaluation reports."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from ..logging import USAGE_LOG_PATH


def usage_rows(path: Path = USAGE_LOG_PATH) -> list[dict[str, str]]:
    """Load usage rows so a benchmark run can be reported independently of history."""
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def summarize_cost_rows(rows: list[dict[str, str]]) -> dict[str, dict[str, float]]:
    """Aggregate exact token, latency, actual, and counterfactual cost totals."""
    totals: defaultdict[str, dict[str, float]] = defaultdict(
        lambda: {
            "calls": 0.0,
            "prompt_tokens": 0.0,
            "completion_tokens": 0.0,
            "latency_ms": 0.0,
            "actual_cost_usd": 0.0,
            "flagship_equivalent_cost_usd": 0.0,
            "routing_savings_usd": 0.0,
        }
    )
    for row in rows:
        key = f"{row['component']}:{row['tier']}"
        total = totals[key]
        total["calls"] += 1
        for metric in tuple(total)[1:]:
            total[metric] += float(row[metric])
    return {key: dict(value) for key, value in sorted(totals.items())}


def model_cost_breakdown(path: Path = USAGE_LOG_PATH) -> dict[str, dict[str, float]]:
    """Return exact totals for every row currently stored in the usage log."""
    return summarize_cost_rows(usage_rows(path))
