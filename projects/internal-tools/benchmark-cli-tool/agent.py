"""Tool-calling agent for questions over the local document library."""

from __future__ import annotations

import json
from typing import Any

from llm import call_llm
from schema import QAResponse
from tools import TOOLS, execute_tool

AGENT_SYSTEM_PROMPT = """You answer questions using only the company document library.
Use the retrieval tools in this order whenever context is needed:
1. list_docs() to discover exact filenames.
2. search_docs(query) to find relevant passages.
3. read_doc(filename, section) to read the source text before answering.
You may repeat search or read calls when needed, but do not invent filenames.
Return exactly a JSON object with answer (string), confidence (number 0.0-1.0),
and source_quote (string). If the documents do not contain the answer, say so,
set confidence to 0.0, and set source_quote to 'N/A'. Tool errors are context
failures to report, not reasons to crash.
"""


def _response_from_content(content: str | None) -> QAResponse:
    """Parse the model's final JSON, with a safe refusal fallback for malformed text."""
    if not content or not content.strip():
        return QAResponse(
            answer="The document does not contain the required information.",
            confidence=0.0,
            source_quote="N/A",
        )
    try:
        return QAResponse.model_validate_json(content)
    except ValueError:
        try:
            return QAResponse.model_validate(json.loads(content))
        except (ValueError, TypeError):
            return QAResponse(answer=content.strip(), confidence=0.0, source_quote="N/A")


def run_agent(question: str, tier: str = "cheap", max_iterations: int = 5) -> QAResponse:
    """Run a bounded tool-calling conversation and return a validated answer."""
    if not question.strip():
        raise ValueError("question must not be empty.")
    if max_iterations < 1:
        raise ValueError("max_iterations must be at least 1.")

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": question.strip()},
    ]
    for _ in range(max_iterations):
        completion = call_llm(tier=tier, messages=messages, tools=TOOLS)
        message = completion.choices[0].message
        if not message.tool_calls:
            return _response_from_content(message.content)

        assistant_message: dict[str, Any] = {
            "role": "assistant",
            "content": message.content or "",
            "tool_calls": [call.model_dump() for call in message.tool_calls],
        }
        messages.append(assistant_message)
        for tool_call in message.tool_calls:
            try:
                arguments = json.loads(tool_call.function.arguments or "{}")
                if not isinstance(arguments, dict):
                    raise ValueError("tool arguments must be a JSON object")
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                result: Any = f"Error: Invalid tool arguments: {exc}"
            else:
                result = execute_tool(tool_call.function.name, arguments)
            if not isinstance(result, str):
                result = json.dumps(result, ensure_ascii=False)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )

    return QAResponse(
        answer="The agent reached its tool-call limit before completing the answer.",
        confidence=0.0,
        source_quote="N/A",
    )
