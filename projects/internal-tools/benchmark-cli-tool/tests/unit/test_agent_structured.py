"""Offline regression test for validated final agent responses."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from benchmark_cli import agent
from benchmark_cli.models import QAResponse


@pytest.mark.unit
def test_non_json_planning_turn_uses_validated_final_answer() -> None:
    """Ensure a non-JSON planning turn cannot become the CLI's final answer."""
    original_call_llm = agent.call_llm
    original_structured_call = agent.call_llm_messages_structured
    structured_calls: list[dict[str, Any]] = []

    def fake_call_llm(**_: Any) -> Any:
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="This deliberately is not JSON.", tool_calls=None
                    )
                )
            ]
        )

    def fake_structured_call(**kwargs: Any) -> QAResponse:
        structured_calls.append(kwargs)
        return QAResponse(
            answer="Validated answer.",
            confidence=0.9,
            source_quote="Evidence from the document.",
        )

    agent.call_llm = fake_call_llm
    agent.call_llm_messages_structured = fake_structured_call
    try:
        metadata: dict[str, Any] = {}
        response = agent.run_agent("Give a grounded answer.", metadata=metadata)
    finally:
        agent.call_llm = original_call_llm
        agent.call_llm_messages_structured = original_structured_call

    assert response.answer == "Validated answer."
    assert 0.0 <= response.confidence <= 1.0
    assert structured_calls, "The final response was not requested as structured output."
    assert metadata["schema_valid"] is True
