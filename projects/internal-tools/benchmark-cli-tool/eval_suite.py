"""Run the Phase 4 routed evaluation and produce a cost/performance report."""

from __future__ import annotations

import contextlib
import csv
import io
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from agent import run_agent
from logger import USAGE_LOG_PATH
from router import classify_query
from schema import QAResponse

RESULTS_PATH = Path(__file__).with_name("eval_results.txt")


@dataclass(frozen=True, slots=True)
class EvalCase:
    question: str
    category: str
    expected_tier: str
    expected_confidence: float | None = None


EVAL_CASES: tuple[EvalCase, ...] = (
    EvalCase("What are the core working hours for remote team members?", "easy", "cheap"),
    EvalCase("How many days per week may employees work remotely?", "easy", "cheap"),
    EvalCase("What is the annual equipment stipend?", "easy", "cheap"),
    EvalCase(
        "List all equipment eligible for reimbursement and detail the travel meal policy requirements.",
        "complex",
        "flagship",
    ),
    EvalCase(
        "Analyze how the remote-work approval rule and core-hours requirement interact, including practical risks for managers.",
        "complex",
        "flagship",
    ),
    EvalCase(
        "Synthesize the reimbursement limits, receipt requirements, and submission deadline into an employee compliance checklist.",
        "complex",
        "flagship",
    ),
    EvalCase(
        "Search the documents for a quantum relocation allowance and report whether any matching passage exists.",
        "edge-zero-hit",
        "cheap",
        0.0,
    ),
    EvalCase(
        "Read nonexistent_policy.txt, section Missing Section, and tell me its vacation policy.",
        "edge-missing-document",
        "cheap",
        0.0,
    ),
    EvalCase(
        "Does the supplied policy document describe parental leave benefits?",
        "out-of-bounds",
        "cheap",
        0.0,
    ),
    EvalCase(
        "What is Acme Corp's stock ticker and current share price according to the policy?",
        "out-of-bounds",
        "cheap",
        0.0,
    ),
)


def usage_rows() -> list[dict[str, str]]:
    """Read the current usage log."""
    if not USAGE_LOG_PATH.exists():
        return []
    with USAGE_LOG_PATH.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def cost(row: dict[str, str], input_rate: Decimal, output_rate: Decimal) -> Decimal:
    """Calculate one row's cost using the supplied per-million-token prices."""
    return (
        Decimal(row["prompt_tokens"]) * input_rate
        + Decimal(row["completion_tokens"]) * output_rate
    ) / Decimal(1_000_000)


def run_case(case: EvalCase) -> dict[str, Any]:
    """Route and execute one case while capturing the agent's stdout tool trace."""
    record: dict[str, Any] = {
        "question": case.question,
        "category": case.category,
        "expected_tier": case.expected_tier,
    }
    try:
        selected_tier = classify_query(case.question)
        record["selected_tier"] = selected_tier
        trace_output = io.StringIO()
        with contextlib.redirect_stdout(trace_output):
            response = run_agent(case.question, tier=selected_tier, max_iterations=5)
        record["tool_trace"] = trace_output.getvalue().splitlines()
        record["response"] = response.model_dump()
        record["routing_correct"] = selected_tier == case.expected_tier
        if case.expected_confidence is not None:
            record["refusal_safe"] = response.confidence == case.expected_confidence
        else:
            record["refusal_safe"] = True
        names = [line.split("] ", 1)[-1].split("(", 1)[0] for line in record["tool_trace"]]
        try:
            list_index = names.index("list_docs")
            search_index = next(
                index for index in range(list_index + 1, len(names)) if names[index] == "search_docs"
            )
            read_index = next(
                index for index in range(search_index + 1, len(names)) if names[index] == "read_doc"
            )
            record["chain_ok"] = list_index < search_index < read_index
        except (StopIteration, ValueError):
            record["chain_ok"] = False
        record["status"] = "passed"
    except Exception as exc:  # Keep the ten-case report complete after one failure.
        record.update(
            {
                "status": "error",
                "error": f"{type(exc).__name__}: {exc}",
                "routing_correct": False,
                "refusal_safe": False,
                "chain_ok": False,
                "tool_trace": [],
            }
        )
    return record


def format_table(rows: list[tuple[str, str]]) -> str:
    """Render a compact two-column comparison table."""
    width = max(len(label) for label, _ in rows)
    return "\n".join(f"{label:<{width}} | {value}" for label, value in rows)


def main() -> None:
    """Run all cases, audit costs, and write the final delivery artifact."""
    before = len(usage_rows())
    records = [run_case(case) for case in EVAL_CASES]
    new_rows = usage_rows()[before:]

    routed_cost = sum(
        (cost(row, Decimal("1.00") if row["tier"] == "cheap" else Decimal("5.00"),
               Decimal("6.00") if row["tier"] == "cheap" else Decimal("30.00"))
         for row in new_rows),
        Decimal(0),
    )
    flagship_cost = sum(
        (cost(row, Decimal("5.00"), Decimal("30.00")) for row in new_rows), Decimal(0)
    )
    routed_prompt_tokens = sum(int(row["prompt_tokens"]) for row in new_rows)
    routed_completion_tokens = sum(int(row["completion_tokens"]) for row in new_rows)

    scored = [record for record in records if record["status"] == "passed"]
    easy_hard = [record for record in records if record["category"] in {"easy", "complex"}]
    routing_correct = sum(record["routing_correct"] for record in easy_hard)
    chain_cases = [record for record in records if record["category"] in {"easy", "complex"}]
    chain_correct = sum(record["chain_ok"] for record in chain_cases)
    safety_cases = [record for record in records if record["category"].startswith("edge") or record["category"] == "out-of-bounds"]
    safety_correct = sum(record["refusal_safe"] for record in safety_cases)
    cheap_notes: list[str] = []
    for record in records:
        if record.get("selected_tier") != "cheap":
            continue
        response_text = str(record.get("response", {}).get("answer", ""))
        if record.get("category") in {"easy", "complex"} and not record.get("chain_ok", True):
            cheap_notes.append(f"{record['question']}: chain deviation or execution error")
        elif "tool-call limit" in response_text.lower():
            cheap_notes.append(f"{record['question']}: reached the five-turn tool-call limit")
    if not cheap_notes:
        cheap_notes = ["none observed"]

    lines: list[str] = [
        "PHASE 4 EVALUATION RESULTS",
        "=" * 28,
        "",
        "COST COMPARISON",
        format_table(
            [
                ("Evaluation cases", str(len(EVAL_CASES))),
                ("Recorded API calls", str(len(new_rows))),
                ("Prompt tokens", f"{routed_prompt_tokens:,}"),
                ("Completion tokens", f"{routed_completion_tokens:,}"),
                ("Routed execution cost", f"${routed_cost:.8f}"),
                ("Flagship-only hypothetical", f"${flagship_cost:.8f}"),
                ("Estimated savings", f"${flagship_cost - routed_cost:.8f}"),
            ]
        ),
        "",
        "QUALITY SUMMARY",
        f"Routing accuracy (easy + complex): {routing_correct}/{len(easy_hard)}",
        f"Tool-chain reliability (list -> search -> read): {chain_correct}/{len(chain_cases)}",
        f"Edge/refusal safety: {safety_correct}/{len(safety_cases)}",
        "Cheap-tier degradation notes:",
        *[f"- {note}" for note in cheap_notes],
        "",
        "QUESTION RESULTS",
    ]
    for index, record in enumerate(records, start=1):
        lines.extend(
            [
                f"{index}. [{record['category']}] {record['question']}",
                f"   selected_tier: {record.get('selected_tier', 'N/A')} | status: {record['status']}",
                f"   tool_trace: {record.get('tool_trace', [])}",
                f"   QAResponse: {record.get('response', record.get('error'))}",
            ]
        )
    report = "\n".join(lines) + "\n"
    RESULTS_PATH.write_text(report, encoding="utf-8")
    print(report, end="")


if __name__ == "__main__":
    main()
