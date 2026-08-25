"""Opt-in, billable verification of the shared OpenAI gateway."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from benchmark_cli.providers.openai import call_llm
from benchmark_cli.telemetry.usage import USAGE_LOG_PATH

pytestmark = pytest.mark.live


def _rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def test_live_gateway_records_one_call_per_tier() -> None:
    before = len(_rows(USAGE_LOG_PATH))
    for tier in ("cheap", "flagship"):
        completion = call_llm(tier, [{"role": "user", "content": "Say hello in one word."}])
        assert completion.choices and completion.choices[0].message.content
    rows = _rows(USAGE_LOG_PATH)[before:]
    assert {row["tier"] for row in rows} >= {"cheap", "flagship"}
