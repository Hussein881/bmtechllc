"""The sole gateway for OpenAI chat-completions calls in this application."""

from __future__ import annotations

from typing import Any, Sequence

from openai import OpenAI
from openai.types.chat import ChatCompletion

from config import OPENAI_API_KEY, get_model_config
from logger import log_usage

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """Create the SDK client lazily so importing this module needs no credential."""
    global _client
    if _client is None:
        if not OPENAI_API_KEY or OPENAI_API_KEY == "your_openai_api_key_here":
            raise RuntimeError(
                "OPENAI_API_KEY is not configured. Set it to a valid API key in .env."
            )
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def _question_from_messages(messages: Sequence[dict[str, Any]]) -> str:
    """Extract the latest plain-text user prompt for cost telemetry."""
    for message in reversed(messages):
        if message.get("role") != "user":
            continue
        content = message.get("content", "")
        if isinstance(content, str):
            return content
        return str(content)
    return ""


def call_llm(
    tier: str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    response_format: Any | None = None,
) -> ChatCompletion:
    """Call the configured tier, log token telemetry, and return its completion.

    Every OpenAI model invocation in this project must use this function; other
    modules must not instantiate the SDK client or call the OpenAI API directly.
    """
    if not messages:
        raise ValueError("messages must contain at least one chat message.")

    model_config = get_model_config(tier)
    request: dict[str, Any] = {
        "model": model_config.model,
        "messages": messages,
    }
    if tools is not None:
        request["tools"] = tools
    if response_format is not None:
        request["response_format"] = response_format

    completion = _get_client().chat.completions.create(**request)
    usage = completion.usage
    log_usage(
        question=_question_from_messages(messages),
        tier=tier,
        model_config=model_config,
        prompt_tokens=usage.prompt_tokens if usage is not None else 0,
        completion_tokens=usage.completion_tokens if usage is not None else 0,
    )
    return completion
