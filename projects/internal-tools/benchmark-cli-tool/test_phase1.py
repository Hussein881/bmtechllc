"""End-to-end verification for Phase 1's centralized LLM gateway and usage log."""

from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from llm import call_llm
from logger import USAGE_LOG_PATH

PROMPT = "Say hello in one word."
TIERS = ("cheap", "flagship")


def read_usage_rows(path: Path) -> list[dict[str, str]]:
    """Load all rows from the usage log and confirm its expected CSV shape."""
    assert path.exists(), f"Usage log was not created at {path}."
    with path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    assert rows, "Usage log was created but contains no usage records."
    required_fields = {
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
    }
    assert set(rows[0]) == required_fields, "Usage log has an unexpected schema."
    return rows


def assert_valid_completion(completion: Any, tier: str) -> None:
    """Check that a chat completion has at least one non-empty text response."""
    assert completion.model, f"{tier} returned no model identifier."
    assert completion.choices, f"{tier} returned no choices."
    content = completion.choices[0].message.content
    assert isinstance(content, str) and content.strip(), f"{tier} returned empty content."


def assert_valid_usage_row(row: dict[str, str], tier: str) -> None:
    """Validate the token counts and non-negative calculated cost for one call."""
    assert row["tier"] == tier
    assert row["model"], f"{tier} row is missing a model identifier."
    prompt_tokens = int(row["prompt_tokens"])
    completion_tokens = int(row["completion_tokens"])
    assert prompt_tokens > 0, f"{tier} prompt token count must be positive."
    assert completion_tokens > 0, f"{tier} completion token count must be positive."
    try:
        cost = Decimal(row["total_cost_usd"])
        flagship_equivalent = Decimal(row["flagship_equivalent_cost_usd"])
        savings = Decimal(row["routing_savings_usd"])
    except InvalidOperation as exc:
        raise AssertionError(f"{tier} row has an invalid USD cost.") from exc
    assert cost >= 0, f"{tier} row has a negative USD cost."
    assert flagship_equivalent >= cost
    if tier == "cheap":
        assert savings > 0, "A routed cheap-tier agent call must record savings."
    else:
        assert savings == 0, "A flagship-tier agent call has no routing savings."


def main() -> None:
    """Run both configured model tiers and verify their telemetry was persisted."""
    previous_row_count = len(read_usage_rows(USAGE_LOG_PATH)) if USAGE_LOG_PATH.exists() else 0

    for tier in TIERS:
        completion = call_llm(tier, [{"role": "user", "content": PROMPT}])
        assert_valid_completion(completion, tier)

    new_rows = read_usage_rows(USAGE_LOG_PATH)[previous_row_count:]
    matching_rows = [row for row in new_rows if row["question"] == PROMPT]
    assert len(matching_rows) == len(TIERS), "Expected one newly logged call per tier."

    rows_by_tier = {row["tier"]: row for row in matching_rows}
    assert set(rows_by_tier) == set(TIERS), "Usage log did not contain both model tiers."
    for tier in TIERS:
        assert_valid_usage_row(rows_by_tier[tier], tier)

    print("Phase 1 integration test passed: both tiers returned completions and logged usage.")


if __name__ == "__main__":
    main()
