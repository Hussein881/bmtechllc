"""The sole gateway for chat-completion calls used by the answer layer."""

from __future__ import annotations

from collections.abc import Sequence
from time import perf_counter
from typing import Any, TypeVar

from openai import OpenAI
from pydantic import BaseModel

from .config import OPENAI_API_KEY, get_model_config
from .logging import log_usage

_client: OpenAI | None = None
StructuredResponse = TypeVar("StructuredResponse", bound=BaseModel)


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not OPENAI_API_KEY or OPENAI_API_KEY == "your_openai_api_key_here":
            raise RuntimeError("OPENAI_API_KEY is not configured.")
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def _record(completion: Any, *, tier: str, component: str, started_at: float) -> None:
    usage = completion.usage
    log_usage(
        tier=tier,
        component=component,
        prompt_tokens=usage.prompt_tokens if usage else 0,
        completion_tokens=usage.completion_tokens if usage else 0,
        latency_ms=(perf_counter() - started_at) * 1_000,
    )


def call_llm(
    *, tier: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None,
    component: str = "agent",
) -> Any:
    """Call a configured model and record its token/latency/cost telemetry."""
    if not messages:
        raise ValueError("messages must not be empty.")
    request: dict[str, Any] = {"model": get_model_config(tier).model, "messages": messages}
    if tools is not None:
        request["tools"] = tools
    started_at = perf_counter()
    completion = _get_client().chat.completions.create(**request)
    _record(completion, tier=tier, component=component, started_at=started_at)
    return completion


def call_llm_structured(
    *, tier: str, messages: Sequence[dict[str, Any]], response_schema: type[StructuredResponse],
    component: str = "answer_synthesis",
) -> StructuredResponse:
    """Return a Pydantic-validated structured completion and log the call."""
    if not messages:
        raise ValueError("messages must not be empty.")
    started_at = perf_counter()
    completion = _get_client().beta.chat.completions.parse(
        model=get_model_config(tier).model,
        messages=list(messages),
        response_format=response_schema,
    )
    _record(completion, tier=tier, component=component, started_at=started_at)
    parsed = completion.choices[0].message.parsed
    if not isinstance(parsed, response_schema):
        raise RuntimeError("The model did not return the requested structured response.")
    return parsed
