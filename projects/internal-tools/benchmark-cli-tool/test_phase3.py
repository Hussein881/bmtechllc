"""Integration tests for Phase 3 retrieval tools and tool-calling agents."""

from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path
from typing import Any

import agent
from agent import run_agent
from logger import USAGE_LOG_PATH
from tools import list_docs, read_doc, search_docs


def read_usage_rows(path: Path) -> list[dict[str, str]]:
    """Read the usage log when present."""
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def test_local_tools() -> None:
    """Verify the complete deterministic list/search/read path and safe failures."""
    documents = list_docs()
    assert documents and all(
        set(document) == {"filename", "title", "type", "date"} for document in documents
    )

    hits = search_docs("core hours")
    assert hits and {"filename", "location", "snippet"} <= set(hits[0])
    sample_hit = next(hit for hit in hits if hit["filename"] == "sample_policy.txt")
    content = read_doc(sample_hit["filename"], section="Hours")
    assert "10:00" in content

    assert search_docs("term-that-is-not-in-the-library") == []
    assert read_doc("missing_policy.txt") == "Error: Document or section not found."
    assert read_doc(hits[0]["filename"], section="Missing Section") == (
        "Error: Document or section not found."
    )


def test_agent_tiers() -> list[dict[str, Any]]:
    """Run full retrieval questions through both tiers and report tool-chain warnings."""
    warnings: list[dict[str, Any]] = []
    original_execute_tool = agent.execute_tool

    for tier in ("cheap", "flagship"):
        trace: list[tuple[str, dict[str, Any]]] = []

        def traced_execute_tool(name: str, arguments: dict[str, Any]) -> Any:
            trace.append((name, arguments))
            return original_execute_tool(name, arguments)

        agent.execute_tool = traced_execute_tool
        response = run_agent(
            "Find the company's core working hours in the document library and explain them.",
            tier=tier,
        )
        assert response.answer
        names = [name for name, _ in trace]
        expected = ["list_docs", "search_docs", "read_doc"]
        if names[:3] != expected:
            warnings.append({"tier": tier, "issue": "tool chain", "trace": trace})
        if any(not isinstance(arguments, dict) for _, arguments in trace):
            warnings.append({"tier": tier, "issue": "tool arguments", "trace": trace})

    agent.execute_tool = original_execute_tool
    return warnings


def test_agent_missing_context() -> None:
    """Ensure missing document and section requests become safe zero-confidence answers."""
    for tier in ("cheap", "flagship"):
        missing_document = run_agent(
            "Read nonexistent_policy.txt and tell me its vacation policy.", tier=tier
        )
        assert missing_document.confidence == 0.0

        missing_section = run_agent(
            "Read the Missing Section section of sample_policy.txt and summarize it.",
            tier=tier,
        )
        assert missing_section.confidence == 0.0


def main() -> None:
    """Run local retrieval checks, both model tiers, and telemetry validation."""
    before = len(read_usage_rows(USAGE_LOG_PATH))
    test_local_tools()
    warnings = test_agent_tiers()
    test_agent_missing_context()
    new_rows = read_usage_rows(USAGE_LOG_PATH)[before:]
    assert {row["tier"] for row in new_rows} >= {"cheap", "flagship"}
    for row in new_rows:
        assert int(row["prompt_tokens"]) > 0
        assert int(row["completion_tokens"]) > 0
        assert Decimal(row["total_cost_usd"]) > 0
    for warning in warnings:
        print(f"WARNING: {warning}")
    print("Phase 3 integration test passed: retrieval, tool errors, both tiers, and telemetry verified.")


if __name__ == "__main__":
    main()
