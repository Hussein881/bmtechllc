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
from config import MODEL_TIERS, ModelConfig
from logger import USAGE_LOG_PATH
from prompts import AGENT_PROMPT_VERSION
from router import classify_query

RESULTS_PATH = Path(__file__).with_name("eval_results.txt")


@dataclass(frozen=True, slots=True)
class EvalCase:
    question: str
    category: str
    expected_tier: str
    expected_confidence: float | None = None


EVAL_CASES: tuple[EvalCase, ...] = (
    # --- Easy Questions (Target: cheap tier) ---
    EvalCase(
        "What are the core working hours for remote team members?",
        "easy",
        "cheap",
    ),
    EvalCase(
        "How many days per week may employees work remotely?",
        "easy",
        "cheap",
    ),
    EvalCase(
        "What is the annual equipment stipend?",
        "easy",
        "cheap",
    ),
    # --- Complex Questions (Target: flagship tier) ---
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
    # --- Edge Cases (Zero-hit search & Missing Document) ---
    EvalCase(
        "Search the documents for a quantum relocation allowance and report whether any matching passage exists.",
        "edge-zero-hit",
        "cheap",
        0.0,
    ),
    EvalCase(
        "Read the Nonexistent Section section of sample_policy.txt and summarize it.",
        "edge-missing-section",
        "cheap",
        0.0,
    ),
    # --- Out-of-bounds Questions (Grounded Refusal) ---
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


def cost(row: dict[str, str], model_config: ModelConfig) -> Decimal:
    """Calculate one row's cost from the centrally configured model rates."""
    return (
        Decimal(row["prompt_tokens"]) * Decimal(str(model_config.input_cost_per_million))
        + Decimal(row["completion_tokens"]) * Decimal(str(model_config.output_cost_per_million))
    ) / Decimal(1_000_000)


def run_case(case: EvalCase, forced_tier: str | None = None) -> dict[str, Any]:
    """Route and execute one case while capturing the agent's stdout tool trace."""
    record: dict[str, Any] = {
        "question": case.question,
        "category": case.category,
        "expected_tier": case.expected_tier,
        "prompt_version": AGENT_PROMPT_VERSION,
    }
    try:
        selected_tier = forced_tier or classify_query(case.question)
        record["selected_tier"] = selected_tier
        record["selection_mode"] = "forced" if forced_tier else "routed"
        trace_output = io.StringIO()
        agent_metadata: dict[str, Any] = {}
        with contextlib.redirect_stdout(trace_output):
            response = run_agent(
                case.question,
                tier=selected_tier,
                max_iterations=5,
                metadata=agent_metadata,
            )
        record["tool_trace"] = trace_output.getvalue().splitlines()
        record["response"] = response.model_dump()
        record["schema_valid"] = agent_metadata.get("schema_valid", False)
        record["schema_error"] = agent_metadata.get("schema_error")
        record["routing_correct"] = forced_tier is None and selected_tier == case.expected_tier
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


def run_mode(label: str, cases: tuple[EvalCase, ...], forced_tier: str | None = None) -> dict[str, Any]:
    """Run one evaluation mode and isolate its telemetry rows."""
    before = len(usage_rows())
    records = [run_case(case, forced_tier) for case in cases]
    rows = usage_rows()[before:]
    return {"label": label, "records": records, "rows": rows}


def total_cost(rows: list[dict[str, str]]) -> Decimal:
    """Calculate recorded cost using the configured rate for each logged tier."""
    return sum((cost(row, MODEL_TIERS[row["tier"]]) for row in rows), Decimal(0))


def format_table(rows: list[tuple[str, str]]) -> str:
    """Render a compact two-column comparison table."""
    width = max(len(label) for label, _ in rows)
    return "\n".join(f"{label:<{width}} | {value}" for label, value in rows)


def main() -> None:
    """Run routed, flagship-only, and forced-cheap benchmarks."""
    routed = run_mode("Routed", EVAL_CASES)
    flagship_only = run_mode("Flagship-only", EVAL_CASES, forced_tier="flagship")
    complex_cases = tuple(case for case in EVAL_CASES if case.category == "complex")
    cheap_stress = run_mode("Cheap stress", complex_cases, forced_tier="cheap")

    routed_records = routed["records"]
    easy_hard = [record for record in routed_records if record["category"] in {"easy", "complex"}]
    routing_correct = sum(record["routing_correct"] for record in easy_hard)
    chain_correct = sum(record["chain_ok"] for record in easy_hard)
    safety_cases = [
        record
        for record in routed_records
        if record["category"].startswith("edge") or record["category"] == "out-of-bounds"
    ]
    safety_correct = sum(record["refusal_safe"] for record in safety_cases)
    schema_failures = [record for record in routed_records if not record.get("schema_valid")]

    cheap_notes: list[str] = []
    for record in cheap_stress["records"]:
        response = record.get("response", {})
        if record["status"] != "passed":
            cheap_notes.append(f"{record['question']}: execution error")
        elif not record.get("schema_valid"):
            cheap_notes.append(f"{record['question']}: invalid structured response")
        elif not record.get("chain_ok"):
            cheap_notes.append(f"{record['question']}: retrieval chain deviation")
        elif response.get("confidence", 0.0) == 0.0:
            cheap_notes.append(f"{record['question']}: refused a complex retrieval task")
    if not cheap_notes:
        cheap_notes = ["none observed in the forced-cheap complex benchmark"]

    routed_cost = total_cost(routed["rows"])
    flagship_cost = total_cost(flagship_only["rows"])
    lines: list[str] = [
        "PHASE 4 EVALUATION RESULTS",
        "=" * 28,
        "",
        "COST COMPARISON (MEASURED RUNS)",
        f"Agent prompt version: {AGENT_PROMPT_VERSION}",
        format_table(
            [
                ("Routed API calls", str(len(routed["rows"]))),
                ("Routed execution cost", f"${routed_cost:.8f}"),
                ("Flagship-only API calls", str(len(flagship_only["rows"]))),
                ("Flagship-only execution cost", f"${flagship_cost:.8f}"),
                ("Measured routing savings", f"${flagship_cost - routed_cost:.8f}"),
                ("Forced-cheap complex API calls", str(len(cheap_stress["rows"]))),
                ("Forced-cheap complex cost", f"${total_cost(cheap_stress['rows']):.8f}"),
            ]
        ),
        "",
        "QUALITY SUMMARY (ROUTED RUN)",
        f"Routing accuracy (easy + complex): {routing_correct}/{len(easy_hard)}",
        f"Tool-chain reliability (list -> search -> read): {chain_correct}/{len(easy_hard)}",
        f"Edge/refusal safety: {safety_correct}/{len(safety_cases)}",
        f"Structured-output validation failures: {len(schema_failures)}",
        "Forced-cheap degradation notes:",
        *[f"- {note}" for note in cheap_notes],
    ]
    for mode in (routed, flagship_only, cheap_stress):
        lines.extend(["", f"{mode['label'].upper()} QUESTION RESULTS"])
        for index, record in enumerate(mode["records"], start=1):
            lines.extend(
                [
                    f"{index}. [{record['category']}] {record['question']}",
                    f"   selected_tier: {record.get('selected_tier', 'N/A')} | status: {record['status']} | schema_valid: {record.get('schema_valid', False)}",
                    f"   tool_trace: {record.get('tool_trace', [])}",
                    f"   QAResponse: {record.get('response', record.get('error'))}",
                ]
            )
    report = "\n".join(lines) + "\n"
    RESULTS_PATH.write_text(report, encoding="utf-8")
    print(report, end="")


if __name__ == "__main__":
    main()
