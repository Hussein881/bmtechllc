"""Tool-calling agent for questions over the local document library."""

from __future__ import annotations

import json
import argparse
from typing import Any

from llm import call_llm
from prompts import AGENT_SYSTEM_PROMPT
from schema import QAResponse
from tools import TOOLS, execute_tool


def _response_from_content(
    content: str | None, metadata: dict[str, Any] | None = None
) -> QAResponse:
    """Parse validated JSON, recording malformed structured-output failures."""
    if not content or not content.strip():
        if metadata is not None:
            metadata["schema_valid"] = False
            metadata["schema_error"] = "empty model response"
        return QAResponse(
            answer="The model returned no structured answer.",
            confidence=0.0,
            source_quote="N/A",
        )
    try:
        response = QAResponse.model_validate_json(content)
    except ValueError as exc:
        if metadata is not None:
            metadata["schema_valid"] = False
            metadata["schema_error"] = str(exc)
        print("[SCHEMA VALIDATION FAILED] Final model response was not a valid QAResponse.")
        return QAResponse(
            answer="The model returned an invalid structured response.",
            confidence=0.0,
            source_quote="N/A",
        )
    if metadata is not None:
        metadata["schema_valid"] = True
    return response


def _finalise_response(
    content: str | None,
    *,
    no_matching_evidence: bool,
    metadata: dict[str, Any] | None,
) -> QAResponse:
    """Parse a final response and apply retrieval-based refusal safeguards."""
    return _enforce_retrieval_refusal(
        _response_from_content(content, metadata),
        no_matching_evidence=no_matching_evidence,
    )


def _enforce_retrieval_refusal(response: QAResponse, no_matching_evidence: bool) -> QAResponse:
    """Prevent unsupported confidence after retrieval reports no matching evidence."""
    if no_matching_evidence and response.source_quote == "N/A" and response.confidence > 0.0:
        return response.model_copy(update={"confidence": 0.0})
    return response


def run_agent(
    question: str,
    tier: str = "cheap",
    max_iterations: int = 5,
    metadata: dict[str, Any] | None = None,
) -> QAResponse:
    """Run a bounded tool-calling conversation and return a validated answer."""
    if not question.strip():
        raise ValueError("question must not be empty.")
    if max_iterations < 1:
        raise ValueError("max_iterations must be at least 1.")

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": question.strip()},
    ]
    zero_hit_seen = False
    search_hit_seen = False
    for _ in range(max_iterations):
        completion = call_llm(tier=tier, messages=messages, tools=TOOLS)
        message = completion.choices[0].message
        if not message.tool_calls:
            return _finalise_response(
                message.content,
                no_matching_evidence=zero_hit_seen and not search_hit_seen,
                metadata=metadata,
            )

        assistant_message: dict[str, Any] = {
            "role": "assistant",
            "content": message.content or "",
            "tool_calls": [call.model_dump() for call in message.tool_calls],
        }
        messages.append(assistant_message)
        tool_error_seen = False
        for tool_call in message.tool_calls:
            print(_format_tool_call(tool_call.function.name, tool_call.function.arguments))
            try:
                arguments = json.loads(tool_call.function.arguments or "{}")
                if not isinstance(arguments, dict):
                    raise ValueError("tool arguments must be a JSON object")
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                result: Any = f"Error: Invalid tool arguments: {exc}"
            else:
                result = execute_tool(tool_call.function.name, arguments)
            if tool_call.function.name == "search_docs":
                if isinstance(result, list) and result:
                    search_hit_seen = True
                elif result == []:
                    zero_hit_seen = True
            if not isinstance(result, str):
                result = json.dumps(result, ensure_ascii=False)
            tool_error_seen = tool_error_seen or result.startswith("Error:")
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )
        if tool_error_seen:
            # Preserve the error as a role=tool message, then give the model
            # one final turn without tools so it can produce a zero-confidence
            # explanation instead of repeatedly retrying the failed lookup.
            final_completion = call_llm(tier=tier, messages=messages)
            return _finalise_response(
                final_completion.choices[0].message.content,
                no_matching_evidence=zero_hit_seen and not search_hit_seen,
                metadata=metadata,
            )

    # The tool-call budget is exhausted, but the accumulated tool messages may
    # still contain enough evidence for a final answer. Give the model one
    # synthesis turn without tools; the five-call retrieval limit remains intact.
    final_completion = call_llm(tier=tier, messages=messages)
    return _finalise_response(
        final_completion.choices[0].message.content,
        no_matching_evidence=zero_hit_seen and not search_hit_seen,
        metadata=metadata,
    )


def _format_tool_call(name: str, raw_arguments: str | None) -> str:
    """Format an executed tool call for the CLI trace."""
    try:
        arguments = json.loads(raw_arguments or "{}")
    except (json.JSONDecodeError, TypeError):
        arguments = {}
    if name == "list_docs":
        return "[TOOL CALL] list_docs()"
    if name == "search_docs":
        return f'[TOOL CALL] search_docs({json.dumps(arguments.get("query", ""))})'
    if name == "read_doc":
        filename = json.dumps(arguments.get("filename", ""))
        section = arguments.get("section")
        if section is None:
            return f"[TOOL CALL] read_doc({filename})"
        return f"[TOOL CALL] read_doc({filename}, {json.dumps(section)})"
    return f"[TOOL CALL] {name}({raw_arguments or '{}'})"


def main() -> None:
    """Run the agent from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question", required=True, help="Question to answer from the documents.")
    parser.add_argument("--tier", choices=("cheap", "flagship"), default="cheap")
    args = parser.parse_args()
    response = run_agent(args.question, tier=args.tier)
    print(response.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
