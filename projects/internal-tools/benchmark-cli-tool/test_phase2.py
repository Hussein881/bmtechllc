"""Live integration verification for Phase 2 routing and structured output."""

from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path

from llm import call_llm_structured
from logger import USAGE_LOG_PATH
from router import classify_query
from schema import QAResponse

EASY_QUESTION = "What color is the sky on a clear day?"
HARD_QUESTION = (
    "A company must choose between a program that reduces costs after six months "
    "and one that immediately improves retention. Analyze the trade-offs, account "
    "for near-term cash-flow and long-term retention priorities, and recommend a plan."
)
DOCUMENT = "On a clear day, the sky appears blue."
STRUCTURED_SYSTEM_PROMPT = """Answer only as a JSON object with these fields:
answer (string), confidence (number from 0.0 to 1.0), and source_quote (string).
Use only the provided document. If the answer is absent, use confidence 0.0 and
source_quote 'N/A'."""


def read_rows(path: Path) -> list[dict[str, str]]:
    """Return telemetry rows from the CSV log, or an empty list when it is absent."""
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def structured_response(tier: str) -> QAResponse:
    """Call one tier and receive an application-validated ``QAResponse``."""
    response = call_llm_structured(
        tier=tier,
        system_prompt=STRUCTURED_SYSTEM_PROMPT,
        prompt=f"Document:\n{DOCUMENT}\n\nQuestion:\n{EASY_QUESTION}",
        response_schema=QAResponse,
    )
    assert isinstance(response.confidence, float)
    assert 0.0 <= response.confidence <= 1.0
    return response


def assert_valid_telemetry(rows: list[dict[str, str]]) -> None:
    """Ensure every live call produced billable, well-formed telemetry."""
    assert len(rows) == 4, f"Expected four new model calls, found {len(rows)}."
    assert [row["tier"] for row in rows].count("cheap") == 3
    assert [row["tier"] for row in rows].count("flagship") == 1
    for row in rows:
        assert int(row["prompt_tokens"]) > 0
        assert int(row["completion_tokens"]) > 0
        assert Decimal(row["total_cost_usd"]) > 0


def main() -> None:
    """Execute Phase 2's live routing, JSON parsing, and telemetry checks."""
    existing_rows = read_rows(USAGE_LOG_PATH)

    assert classify_query(EASY_QUESTION) == "cheap"
    assert classify_query(HARD_QUESTION) == "flagship"
    for tier in ("cheap", "flagship"):
        response = structured_response(tier)
        assert response.answer
        assert response.source_quote

    assert_valid_telemetry(read_rows(USAGE_LOG_PATH)[len(existing_rows) :])
    print("Phase 2 integration test passed: routing, structured JSON, and telemetry verified.")


if __name__ == "__main__":
    main()
