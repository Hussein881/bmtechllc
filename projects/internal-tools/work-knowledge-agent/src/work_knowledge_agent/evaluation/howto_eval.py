"""Evaluation helpers for the Phase 3 How-To workflow."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Any, Sequence

from work_knowledge_agent.agents.howto_agent import REQUIRED_SECTIONS
from work_knowledge_agent.models import LLMClient
from work_knowledge_agent.workflows.howto_workflow import HowToWorkflowConfig, run_howto_workflow


@dataclass(frozen=True)
class HowToEvalCase:
	id: str
	task: str
	expected_commands: tuple[str, ...] = ()
	expected_sources: tuple[str, ...] = ()


def load_howto_eval_cases(path: Path) -> list[HowToEvalCase]:
	if not path.exists() or not path.read_text(encoding="utf-8").strip():
		return []
	rows = json.loads(path.read_text(encoding="utf-8"))
	if not isinstance(rows, list):
		raise ValueError("How-To eval cases file must contain a JSON array")

	cases: list[HowToEvalCase] = []
	for idx, row in enumerate(rows, start=1):
		if not isinstance(row, dict):
			continue
		task = str(row.get("task", "")).strip()
		if not task:
			continue
		case_id = str(row.get("id", "")).strip() or f"howto-case-{idx}"
		expected_commands = row.get("expected_commands", [])
		expected_sources = row.get("expected_sources", [])
		if not isinstance(expected_commands, list):
			expected_commands = []
		if not isinstance(expected_sources, list):
			expected_sources = []
		cases.append(
			HowToEvalCase(
				id=case_id,
				task=task,
				expected_commands=tuple(str(value) for value in expected_commands if str(value).strip()),
				expected_sources=tuple(str(value) for value in expected_sources if str(value).strip()),
			)
		)
	return cases


def evaluate_howto_cases(
	cases: Sequence[HowToEvalCase],
	*,
	chunks_path: Path,
	metadata_path: Path,
	keyword_index_path: Path,
	vector_index_path: Path,
	config: HowToWorkflowConfig,
	llm_client: LLMClient | None = None,
	trials_per_case: int = 1,
) -> dict[str, Any]:
	total_cases = 0
	total_runs = 0
	supported = 0
	citation_ok = 0
	required_sections_ok = 0
	expected_command_match = 0
	expected_source_match = 0
	latencies: list[float] = []
	answer_latencies: list[float] = []

	per_case: list[dict[str, Any]] = []
	for case in cases:
		total_cases += 1
		trial_rows: list[dict[str, Any]] = []
		for trial_index in range(trials_per_case):
			total_runs += 1
			try:
				result = run_howto_workflow(
					task=case.task,
					chunks_path=chunks_path,
					metadata_path=metadata_path,
					keyword_index_path=keyword_index_path,
					vector_index_path=vector_index_path,
					config=config,
					llm_client=llm_client,
				)
			except Exception as exc:  # noqa: BLE001
				trial_rows.append(
					{
						"trial_index": trial_index + 1,
						"supported": False,
						"citation_ok": False,
						"required_sections_ok": False,
						"expected_command_match": False,
						"expected_source_match": False,
						"expected_commands": list(case.expected_commands),
						"expected_sources": list(case.expected_sources),
						"citation_sources": [],
						"retrieval_hit_count": 0,
						"stage_times_ms": {},
						"generation_metadata": {},
						"guardrail_status": {},
						"answer": "",
						"error": str(exc),
					}
				)
				continue

			answer_text = result.response.answer
			sections_ok = all(f"## {section}" in answer_text for section in REQUIRED_SECTIONS)
			command_ok = _contains_all(answer_text, case.expected_commands)
			citation_sources = [str(citation.get("source_file", "")) for citation in result.response.citations]
			source_ok = _source_match(citation_sources, case.expected_sources)

			if result.response.supported:
				supported += 1
			if result.guardrail_status.get("citation_ok"):
				citation_ok += 1
			if sections_ok:
				required_sections_ok += 1
			if command_ok:
				expected_command_match += 1
			if source_ok:
				expected_source_match += 1

			latencies.append(float(result.stage_times_ms.get("total", 0.0)))
			answer_latencies.append(float(result.stage_times_ms.get("answer_generation", 0.0)))

			trial_rows.append(
				{
					"trial_index": trial_index + 1,
					"supported": result.response.supported,
					"citation_ok": result.guardrail_status.get("citation_ok"),
					"required_sections_ok": sections_ok,
					"expected_command_match": command_ok,
					"expected_source_match": source_ok,
					"expected_commands": list(case.expected_commands),
					"expected_sources": list(case.expected_sources),
					"citation_sources": citation_sources,
					"retrieval_hit_count": len(result.retrieval_hits),
					"stage_times_ms": result.stage_times_ms,
					"generation_metadata": result.generation_metadata,
					"guardrail_status": result.guardrail_status,
					"answer": answer_text,
				}
			)

		per_case.append(
			{
				"id": case.id,
				"task": case.task,
				"expected_commands": list(case.expected_commands),
				"expected_sources": list(case.expected_sources),
				"trials": trial_rows,
				"summary": {
					"supported_rate_pct": round(_percent(sum(1 for row in trial_rows if row["supported"]), trials_per_case), 3),
					"citation_ok_rate_pct": round(_percent(sum(1 for row in trial_rows if row["citation_ok"]), trials_per_case), 3),
					"required_sections_rate_pct": round(_percent(sum(1 for row in trial_rows if row["required_sections_ok"]), trials_per_case), 3),
					"expected_command_match_rate_pct": round(_percent(sum(1 for row in trial_rows if row["expected_command_match"]), trials_per_case), 3),
					"expected_source_match_rate_pct": round(_percent(sum(1 for row in trial_rows if row["expected_source_match"]), trials_per_case), 3),
				},
			}
		)

	return {
		"total_cases": total_cases,
		"trials_per_case": trials_per_case,
		"total_runs": total_runs,
		"metrics": {
			"supported_rate_pct": round(_percent(supported, total_runs), 3),
			"citation_ok_rate_pct": round(_percent(citation_ok, total_runs), 3),
			"required_sections_rate_pct": round(_percent(required_sections_ok, total_runs), 3),
			"expected_command_match_rate_pct": round(_percent(expected_command_match, total_runs), 3),
			"expected_source_match_rate_pct": round(_percent(expected_source_match, total_runs), 3),
			"latency_p50_ms": round(float(median(latencies)) if latencies else 0.0, 3),
			"latency_p95_ms": round(_p95(latencies), 3),
			"answer_generation_p50_ms": round(float(median(answer_latencies)) if answer_latencies else 0.0, 3),
			"answer_generation_p95_ms": round(_p95(answer_latencies), 3),
		},
		"per_case": per_case,
	}


def _contains_all(text: str, expected: Sequence[str]) -> bool:
	value = (text or "").lower()
	for token in expected:
		if str(token).lower() not in value:
			return False
	return True if expected else True


def _source_match(paths: Sequence[str], expected_substrings: Sequence[str]) -> bool:
	if not expected_substrings:
		return True
	for expected in expected_substrings:
		if any(expected in value for value in paths):
			return True
	return False


def _percent(num: int, den: int) -> float:
	return (num / den * 100.0) if den else 0.0


def _p95(values: list[float]) -> float:
	if not values:
		return 0.0
	sorted_vals = sorted(values)
	idx = min(len(sorted_vals) - 1, int(round(0.95 * (len(sorted_vals) - 1))))
	return float(sorted_vals[idx])