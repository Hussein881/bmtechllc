"""Offline integration checks for deterministic retrieval and agent safety."""

from __future__ import annotations

import json
import re
from types import SimpleNamespace
from typing import Any

import pytest

from benchmark_cli import agent, retrieval
from benchmark_cli.models import QAResponse


@pytest.mark.integration
def test_local_tools(document_library: object, monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise list, keyword search, section reads, and safe misses against fixtures."""
    monkeypatch.setenv("SEARCH_MODE", "keyword")
    documents = retrieval.list_docs()
    assert documents and all(set(document) == {"filename", "title", "type", "date"} for document in documents)

    filename = documents[0]["filename"]
    full_document = retrieval.read_doc(filename)
    terms = re.findall(r"[A-Za-z]{4,}", full_document)
    assert terms
    hits = retrieval.search_docs(terms[0])
    assert hits and {"filename", "location", "snippet"} <= set(hits[0])
    assert retrieval.search_docs("term-that-is-not-in-the-library") == []
    assert retrieval.read_doc("missing_policy.txt") == "Error: Document or section not found."


@pytest.mark.integration
def test_agent_missing_context_returns_safe_refusal(
    document_library: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed document lookup must produce a zero-confidence final response."""
    filename = retrieval.list_docs()[0]["filename"]

    def fake_call_llm(**_: Any) -> Any:
        function = SimpleNamespace(name="read_doc", arguments=json.dumps({"filename": "missing.txt"}))
        tool_call = SimpleNamespace(
            id="test-tool-call",
            function=function,
            model_dump=lambda: {
                "id": "test-tool-call",
                "type": "function",
                "function": {"name": "read_doc", "arguments": json.dumps({"filename": "missing.txt"})},
            },
        )
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=None, tool_calls=[tool_call]))]
        )

    def fake_structured_call(**_: Any) -> QAResponse:
        return QAResponse(answer="Not found.", confidence=0.8, source_quote="N/A")

    monkeypatch.setattr(agent, "call_llm", fake_call_llm)
    monkeypatch.setattr(agent, "call_llm_messages_structured", fake_structured_call)
    response = agent.run_agent(f"Read {filename} and summarize it.")
    assert response.confidence == 0.0
    assert response.source_quote == "N/A"
