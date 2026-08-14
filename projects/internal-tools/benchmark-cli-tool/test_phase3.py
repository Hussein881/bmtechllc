"""Integration tests for Phase 3 retrieval tools and tool-calling agents."""

from __future__ import annotations

import csv
import json
import os
import re
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import agent
from agent import run_agent
from logger import USAGE_LOG_PATH
from tools import _section_blocks, list_docs, read_doc, search_docs

PHASE3_RESULTS_PATH = Path(__file__).with_name("phase3_results.json")


def read_usage_rows(path: Path) -> list[dict[str, str]]:
    """Read the usage log when present."""
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def test_local_tools() -> None:
    """Verify the complete deterministic list/search/read path and safe failures."""
    previous_mode = os.environ.get("SEARCH_MODE")
    os.environ["SEARCH_MODE"] = "keyword"
    try:
        documents = list_docs()
        assert documents and all(
            set(document) == {"filename", "title", "type", "date"} for document in documents
        )

        filename = documents[0]["filename"]
        full_document = read_doc(filename)
        assert not full_document.startswith("Error:")
        terms = re.findall(r"[A-Za-z]{4,}", full_document)
        assert terms, "The selected document did not contain a searchable word."
        hits = search_docs(terms[0])
        assert hits and {"filename", "location", "snippet"} <= set(hits[0])
        assert any(hit["filename"] == filename for hit in hits)
        sections = _section_blocks(full_document)
        content = read_doc(filename, section=sections[0][0]) if sections else full_document
        assert content and not content.startswith("Error:")

        assert search_docs("term-that-is-not-in-the-library") == []
        assert read_doc("missing_policy.txt") == "Error: Document or section not found."
        assert read_doc(filename, section="ZZZUnfindableSection999") == (
            "Error: Document or section not found."
        )
    finally:
        if previous_mode is None:
            os.environ.pop("SEARCH_MODE", None)
        else:
            os.environ["SEARCH_MODE"] = previous_mode


def test_agent_tiers() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Run full retrieval questions through both tiers and report tool-chain warnings."""
    warnings: list[dict[str, Any]] = []
    tier_results: dict[str, dict[str, Any]] = {}
    original_execute_tool = agent.execute_tool

    for tier in ("cheap", "flagship"):
        trace: list[tuple[str, dict[str, Any]]] = []

        def traced_execute_tool(name: str, arguments: dict[str, Any]) -> Any:
            trace.append((name, arguments))
            return original_execute_tool(name, arguments)

        agent.execute_tool = traced_execute_tool
        response = run_agent(
            "Find a relevant fact in the document library and explain it.",
            tier=tier,
        )
        assert response.answer
        names = [name for name, _ in trace]
        try:
            list_index = names.index("list_docs")
            search_index = next(
                index for index in range(list_index + 1, len(names)) if names[index] == "search_docs"
            )
            read_index = next(
                index for index in range(search_index + 1, len(names)) if names[index] == "read_doc"
            )
            chain_ok = list_index < search_index < read_index
        except (StopIteration, ValueError):
            chain_ok = False
        arguments_ok = all(isinstance(arguments, dict) for _, arguments in trace)
        tier_warnings: list[str] = []
        if not chain_ok:
            tier_warnings.append("tool chain deviated from list_docs -> search_docs -> read_doc")
            warnings.append({"tier": tier, "issue": "tool chain", "trace": trace})
        if not arguments_ok:
            tier_warnings.append("tool argument formation failed")
            warnings.append({"tier": tier, "issue": "tool arguments", "trace": trace})
        tier_results[tier] = {
            "trace": [{"tool": name, "arguments": arguments} for name, arguments in trace],
            "tool_chain_ok": chain_ok,
            "tool_arguments_ok": arguments_ok,
            "degradation": tier_warnings or ["none observed"],
        }

    agent.execute_tool = original_execute_tool
    return warnings, tier_results


def test_agent_missing_context() -> None:
    """Ensure missing document and section requests become safe zero-confidence answers."""
    original_call_llm = agent.call_llm
    available_documents = list_docs()
    assert available_documents, "The missing-context test requires one document."
    existing_filename = available_documents[0]["filename"]

    def fake_call_llm(
        *, tier: str, messages: list[dict[str, Any]], tools: Any = None
    ) -> Any:
        """Return one missing-file tool call followed by a safe refusal response."""
        if messages[-1]["role"] == "user":
            question = messages[-1]["content"]
            filename = "nonexistent_policy.txt" if "nonexistent" in question else existing_filename
            section = None if "nonexistent" in question else "ZZZUnfindableSection999"
            arguments = {"filename": filename}
            if section is not None:
                arguments["section"] = section
            function = SimpleNamespace(name="read_doc", arguments=json.dumps(arguments))
            tool_call = SimpleNamespace(
                id="test-tool-call",
                function=function,
                model_dump=lambda: {
                    "id": "test-tool-call",
                    "type": "function",
                    "function": {"name": "read_doc", "arguments": json.dumps(arguments)},
                },
            )
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=None, tool_calls=[tool_call]))]
            )
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=json.dumps(
                            {
                                "answer": "The requested information was not found.",
                                "confidence": 0.0,
                                "source_quote": "N/A",
                            }
                        ),
                        tool_calls=None,
                    )
                )
            ]
        )

    agent.call_llm = fake_call_llm
    for tier in ("cheap", "flagship"):
        missing_document = run_agent(
            "Read nonexistent_policy.txt and summarize it.", tier=tier
        )
        assert missing_document.confidence == 0.0

        missing_section = run_agent(
            f"Read the ZZZUnfindableSection999 section of {existing_filename} and summarize it.",
            tier=tier,
        )
        assert missing_section.confidence == 0.0
    agent.call_llm = original_call_llm


def main() -> None:
    """Run local retrieval checks, both model tiers, and telemetry validation."""
    before = len(read_usage_rows(USAGE_LOG_PATH))
    test_local_tools()
    warnings, tier_results = test_agent_tiers()
    test_agent_missing_context()
    new_rows = read_usage_rows(USAGE_LOG_PATH)[before:]
    assert {row["tier"] for row in new_rows} >= {"cheap", "flagship"}
    for row in new_rows:
        assert int(row["prompt_tokens"]) > 0
        assert int(row["completion_tokens"]) > 0
        assert Decimal(row["total_cost_usd"]) > 0
    results = {
        "tiers": tier_results,
        "telemetry": {
            "new_call_count": len(new_rows),
            "tiers_seen": sorted({row["tier"] for row in new_rows}),
        },
        "cheap_tier_degradation": tier_results["cheap"]["degradation"],
    }
    PHASE3_RESULTS_PATH.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    for warning in warnings:
        print(f"WARNING: {warning}")
    print("Phase 3 integration test passed: retrieval, tool errors, both tiers, and telemetry verified.")


if __name__ == "__main__":
    main()
