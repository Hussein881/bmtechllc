"""Opt-in, billable end-to-end test of the retrieval agent."""

from __future__ import annotations

import pytest

from benchmark_cli.agent import run_agent

pytestmark = pytest.mark.live


def test_live_agent_returns_structured_answer(
    document_library: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SEARCH_MODE", "keyword")
    response = run_agent("What is the home-office reimbursement limit?", tier="cheap")
    assert response.answer
    assert 0.0 <= response.confidence <= 1.0
