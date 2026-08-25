"""Opt-in, billable verification of routing and structured output."""

from __future__ import annotations

import pytest

from benchmark_cli.models import QAResponse
from benchmark_cli.providers.openai import call_llm_structured
from benchmark_cli.router import classify_query

pytestmark = pytest.mark.live


def test_live_routing_and_structured_response() -> None:
    assert classify_query("What color is the sky on a clear day?") == "cheap"
    response = call_llm_structured(
        tier="cheap",
        system_prompt="Use only the provided document.",
        prompt="Document: The sky is blue.\n\nQuestion: What color is the sky?",
        response_schema=QAResponse,
    )
    assert response.answer and 0.0 <= response.confidence <= 1.0
