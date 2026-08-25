"""Run the Phase 4 routed evaluation and produce a cost/performance report."""

from __future__ import annotations

import argparse
import contextlib
import csv
import io
import json
import os
import time
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from .. import agent
from ..agent import run_agent
from ..config import MODEL_TIERS, ModelConfig
from ..paths import ARTIFACTS_DIR, artifact_path
from ..prompts import AGENT_PROMPT_VERSION
from ..router import classify_query
from ..telemetry.usage import USAGE_LOG_PATH

RESULTS_PATH = artifact_path("evaluations", "eval_results.txt")


@dataclass(frozen=True, slots=True)
class EvalCase:
    question: str
    category: str
    expected_tier: str
    expected_confidence: float | None = None
    requires_full_read: bool = False
    expected_sources: tuple[str, ...] = ()
    min_sources: int = 1


EVAL_CASES: tuple[EvalCase, ...] = ()


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
        "chain_required": case.requires_full_read,
        "expected_sources": list(case.expected_sources),
        "min_sources": case.min_sources,
        "prompt_version": AGENT_PROMPT_VERSION,
    }
    try:
        selected_tier = forced_tier or classify_query(case.question)
        record["selected_tier"] = selected_tier
        record["selection_mode"] = "forced" if forced_tier else "routed"
        trace_output = io.StringIO()
        retrieved_sources: list[str] = []
        agent_metadata: dict[str, Any] = {}
        original_execute_tool = agent.execute_tool

        def traced_execute_tool(name: str, arguments: dict[str, Any]) -> Any:
            result = original_execute_tool(name, arguments)
            if name == "search_docs" and isinstance(result, list):
                retrieved_sources.extend(
                    str(item["filename"])
                    for item in result
                    if isinstance(item, dict) and isinstance(item.get("filename"), str)
                )
            return result

        started = time.perf_counter()
        agent.execute_tool = traced_execute_tool
        try:
            with contextlib.redirect_stdout(trace_output):
                response = run_agent(
                    case.question,
                    tier=selected_tier,
                    max_iterations=5,
                    metadata=agent_metadata,
                )
        finally:
            agent.execute_tool = original_execute_tool
        record["latency_seconds"] = round(time.perf_counter() - started, 4)
        record["tool_trace"] = trace_output.getvalue().splitlines()
        record["retrieved_sources"] = sorted(set(retrieved_sources))
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
            full_chain_completed = list_index < search_index < read_index
        except (StopIteration, ValueError):
            full_chain_completed = False
        record["chain_ok"] = not case.requires_full_read or full_chain_completed
        record["retrieval_hit"] = set(case.expected_sources).issubset(record["retrieved_sources"])
        record["distinct_sources_ok"] = len(record["retrieved_sources"]) >= case.min_sources
        record["status"] = "passed"
    except Exception as exc:  # Keep the ten-case report complete after one failure.
        record.update(
            {
                "status": "error",
                "error": f"{type(exc).__name__}: {exc}",
                "routing_correct": False,
                "refusal_safe": False,
                "chain_ok": False,
                "retrieval_hit": False,
                "distinct_sources_ok": False,
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


def component_costs(rows: list[dict[str, str]]) -> dict[str, Decimal]:
    """Return separately attributable costs for classifier, agent, and embeddings."""
    values: dict[str, Decimal] = {}
    for row in rows:
        component = row.get("component", "agent")
        values[component] = values.get(component, Decimal(0)) + cost(row, MODEL_TIERS[row["tier"]])
    return values


def run_week2(cases: tuple[EvalCase, ...], modes: tuple[str, ...], search: str, output_dir: Path) -> str:
    """Run reproducible Week 2 arms and persist raw, per-question artifacts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    previous_mode = os.environ.get("SEARCH_MODE")
    os.environ["SEARCH_MODE"] = search
    try:
        arms: list[dict[str, Any]] = []
        for mode in modes:
            if mode == "routed":
                result = run_mode("Routed", cases)
            elif mode == "flagship":
                result = run_mode("Flagship-only", cases, forced_tier="flagship")
            elif mode == "cheap":
                result = run_mode("Cheap-only", cases, forced_tier="cheap")
            else:
                raise ValueError(f"Unsupported Week 2 mode: {mode}")
            artifact = output_dir / f"{mode}.json"
            artifact.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
            arms.append(result)
    finally:
        if previous_mode is None:
            os.environ.pop("SEARCH_MODE", None)
        else:
            os.environ["SEARCH_MODE"] = previous_mode

    routed = next((arm for arm in arms if arm["label"] == "Routed"), None)
    lines = ["WEEK 2 EVALUATION RESULTS", "=" * 25, f"Search mode: {search}", ""]
    for arm in arms:
        records = arm["records"]
        components = component_costs(arm["rows"])
        retrieval_cases = [record for record in records if record["expected_sources"]]
        hit_count = sum(record.get("retrieval_hit", False) for record in retrieval_cases)
        source_cases = [record for record in records if record["min_sources"] > 1]
        source_count = sum(record.get("distinct_sources_ok", False) for record in source_cases)
        lines.extend(
            [
                arm["label"],
                format_table(
                    [
                        ("API calls", str(len(arm["rows"]))),
                        ("Runtime cost", f"${total_cost(arm['rows']):.8f}"),
                        ("Classifier cost", f"${components.get('classifier', Decimal(0)):.8f}"),
                        ("Query embedding cost", f"${components.get('query_embed', Decimal(0)):.8f}"),
                        ("Agent cost", f"${components.get('agent', Decimal(0)):.8f}"),
                        ("Retrieval hit-rate", f"{hit_count}/{len(retrieval_cases)}"),
                        ("Cross-source retrieval", f"{source_count}/{len(source_cases)}"),
                    ]
                ),
                "",
            ]
        )
    if routed:
        routing_cases = [record for record in routed["records"] if record["category"] != "out-of-corpus"]
        lines.append(
            f"Routed tier accuracy: {sum(record.get('routing_correct', False) for record in routing_cases)}/{len(routing_cases)}"
        )
    report = "\n".join(lines) + "\n"
    (output_dir / "summary.txt").write_text(report, encoding="utf-8")
    return report


def main() -> None:
    """Run routed, flagship-only, and forced-cheap benchmarks."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=("week1", "week2"), default="week1")
    parser.add_argument("--modes", default="routed,flagship", help="Week 2 arms: routed,flagship[,cheap].")
    parser.add_argument("--search", choices=("vector", "keyword"), default="vector")
    parser.add_argument("--out", type=Path, default=ARTIFACTS_DIR / "evaluations" / "week2")
    args = parser.parse_args()
    if args.suite == "week2":
        from .cases import load_week2_cases

        modes = tuple(mode.strip() for mode in args.modes.split(",") if mode.strip())
        if not modes:
            raise SystemExit("At least one Week 2 evaluation mode is required.")
        try:
            cases = load_week2_cases()
        except RuntimeError as exc:
            raise SystemExit(str(exc)) from exc
        print(run_week2(cases, modes, args.search, args.out), end="")
        return

    if not EVAL_CASES:
        raise SystemExit(
            "The retired sample-document benchmark is unavailable. "
            "Create reviewed week2_cases.json and run --suite week2 instead."
        )

    routed = run_mode("Routed", EVAL_CASES)
    flagship_only = run_mode("Flagship-only", EVAL_CASES, forced_tier="flagship")
    complex_cases = tuple(case for case in EVAL_CASES if case.category == "complex")
    cheap_stress = run_mode("Cheap stress", complex_cases, forced_tier="cheap")

    routed_records = routed["records"]
    easy_hard = [record for record in routed_records if record["category"] in {"easy", "complex"}]
    routing_correct = sum(record["routing_correct"] for record in easy_hard)
    chain_cases = [record for record in routed_records if record["chain_required"]]
    chain_correct = sum(record["chain_ok"] for record in chain_cases)
    safety_cases = [
        record
        for record in routed_records
        if record["category"].startswith("edge") or record["category"] == "out-of-bounds"
    ]
    safety_correct = sum(record["refusal_safe"] for record in safety_cases)
    schema_failures = [
        record
        for record in routed_records
        if record["status"] == "passed" and record.get("schema_valid") is False
    ]

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
        f"Tool-chain reliability (required full reads): {chain_correct}/{len(chain_cases)}",
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
