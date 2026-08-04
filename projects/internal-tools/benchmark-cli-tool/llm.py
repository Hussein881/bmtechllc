"""The sole gateway for OpenAI chat-completions calls in this application."""

from __future__ import annotations

from typing import Any, Sequence, TypeVar

from openai import OpenAI
from openai.types.chat import ChatCompletion
from pydantic import BaseModel

from config import OPENAI_API_KEY, get_model_config
from logger import log_usage

_client: OpenAI | None = None
StructuredResponse = TypeVar("StructuredResponse", bound=BaseModel)


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


def _log_completion_usage(
    completion: Any, *, tier: str, messages: Sequence[dict[str, Any]]
) -> None:
    """Persist telemetry for either a regular or parsed chat completion."""
    usage = completion.usage
    log_usage(
        question=_question_from_messages(messages),
        tier=tier,
        model_config=get_model_config(tier),
        prompt_tokens=usage.prompt_tokens if usage is not None else 0,
        completion_tokens=usage.completion_tokens if usage is not None else 0,
    )


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
        # GPT-5.6 model tiers require an explicit non-reasoning setting when
        # function tools are used with the Chat Completions endpoint.
        request["reasoning_effort"] = "none"
    if response_format is not None:
        request["response_format"] = response_format

    completion = _get_client().chat.completions.create(**request)
    _log_completion_usage(completion, tier=tier, messages=messages)
    return completion


def call_llm_structured(
    prompt: str,
    system_prompt: str,
    response_schema: type[StructuredResponse],
    tier: str = "cheap",
) -> StructuredResponse:
    """Return an SDK-parsed and Pydantic-validated structured model response.

    This is the application gateway for structured answers. It uses the SDK's
    parsed Chat Completions API, records token usage, and never returns raw JSON.
    """
    if not prompt.strip():
        raise ValueError("prompt must not be empty.")
    if not system_prompt.strip():
        raise ValueError("system_prompt must not be empty.")

    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    model_config = get_model_config(tier)
    completion = _get_client().beta.chat.completions.parse(
        model=model_config.model,
        messages=messages,
        response_format=response_schema,
    )
    _log_completion_usage(completion, tier=tier, messages=messages)

    parsed = completion.choices[0].message.parsed
    if parsed is None:
        refusal = completion.choices[0].message.refusal
        detail = f" Model refusal: {refusal}" if refusal else ""
        raise RuntimeError(f"The model did not return a parsed structured response.{detail}")
    if not isinstance(parsed, response_schema):
        raise RuntimeError("The model returned an unexpected structured response type.")
    return parsed
