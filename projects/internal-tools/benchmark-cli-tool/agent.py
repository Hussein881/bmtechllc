"""Tool-calling agent for questions over the local document library."""

from __future__ import annotations

import json
import argparse
from typing import Any

from llm import call_llm
from schema import QAResponse
from tools import TOOLS, execute_tool

AGENT_SYSTEM_PROMPT = """You answer questions using only the company document library.
Use the retrieval tools in this order whenever context is needed:
1. list_docs() to discover exact filenames.
2. search_docs(query) to find relevant passages.
3. read_doc(filename, section) to read the source text before answering.
For reimbursement and travel questions, use the search query exactly
"reimbursement travel" after list_docs(), then read the matching
"Travel & Expense Reimbursement" section from the relevant document.
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


def _enforce_retrieval_refusal(response: QAResponse, no_matching_evidence: bool) -> QAResponse:
    """Prevent unsupported confidence after retrieval reports no matching evidence."""
    if no_matching_evidence and response.source_quote == "N/A" and response.confidence > 0.0:
        return response.model_copy(update={"confidence": 0.0})
    return response


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
    zero_hit_seen = False
    search_hit_seen = False
    for _ in range(max_iterations):
        completion = call_llm(tier=tier, messages=messages, tools=TOOLS)
        message = completion.choices[0].message
        if not message.tool_calls:
            return _enforce_retrieval_refusal(
                _response_from_content(message.content),
                no_matching_evidence=zero_hit_seen and not search_hit_seen,
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
            return _enforce_retrieval_refusal(
                _response_from_content(final_completion.choices[0].message.content),
                no_matching_evidence=zero_hit_seen and not search_hit_seen,
            )

    return QAResponse(
        answer="The agent reached its tool-call limit before completing the answer.",
        confidence=0.0,
        source_quote="N/A",
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
