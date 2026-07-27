"""Evaluation helpers for the Phase 4 planning workflow."""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Any, Sequence

from work_knowledge_agent.agents.planner_agent import REQUIRED_SECTIONS
from work_knowledge_agent.models import LLMClient
from work_knowledge_agent.workflows.planning_workflow import PlanningWorkflowConfig, run_planning_workflow


@dataclass(frozen=True)
class PlanningEvalCase:
	id: str
	goal: str
	expected_tasks: tuple[str, ...] = ()
	expected_sources: tuple[str, ...] = ()
	expected_supported: bool | None = None
	required_unknown_signals: tuple[str, ...] = ()
	min_open_questions_count: int | None = None


def load_planning_eval_cases(path: Path) -> list[PlanningEvalCase]:
	if not path.exists() or not path.read_text(encoding="utf-8").strip():
		return []
	rows = json.loads(path.read_text(encoding="utf-8"))
	if not isinstance(rows, list):
		raise ValueError("Planning eval cases file must contain a JSON array")

	cases: list[PlanningEvalCase] = []
	for idx, row in enumerate(rows, start=1):
		if not isinstance(row, dict):
			continue
		goal = str(row.get("goal", "")).strip()
		if not goal:
			continue
		case_id = str(row.get("id", "")).strip() or f"plan-case-{idx}"
		expected_tasks = row.get("expected_tasks", [])
		expected_sources = row.get("expected_sources", [])
		if not isinstance(expected_tasks, list):
			expected_tasks = []
		if not isinstance(expected_sources, list):
			expected_sources = []
		expected_supported = row.get("expected_supported")
		if expected_supported is not None and not isinstance(expected_supported, bool):
			expected_supported = None
		required_unknown_signals = row.get("required_unknown_signals", [])
		if not isinstance(required_unknown_signals, list):
			required_unknown_signals = []
		min_open_questions_count = row.get("min_open_questions_count")
		if min_open_questions_count is not None:
			try:
				min_open_questions_count = int(min_open_questions_count)
			except (TypeError, ValueError):
				min_open_questions_count = None
		cases.append(
			PlanningEvalCase(
				id=case_id,
				goal=goal,
				expected_tasks=tuple(str(value) for value in expected_tasks if str(value).strip()),
				expected_sources=tuple(str(value) for value in expected_sources if str(value).strip()),
				expected_supported=expected_supported,
				required_unknown_signals=tuple(str(value) for value in required_unknown_signals if str(value).strip()),
				min_open_questions_count=min_open_questions_count,
			)
		)
	return cases


def evaluate_planning_cases(
	cases: Sequence[PlanningEvalCase],
	*,
	chunks_path: Path,
	metadata_path: Path,
	keyword_index_path: Path,
	vector_index_path: Path,
	config: PlanningWorkflowConfig,
	llm_client: LLMClient | None = None,
	trials_per_case: int = 1,
	strict_source_match: bool = True,
	min_task_token_overlap: float = 0.60,
) -> dict[str, Any]:
	total_cases = 0
	total_runs = 0
	raw_supported = 0
	raw_citation_ok = 0
	supported_expected_ok = 0
	citation_expected_ok = 0
	support_expected_runs = 0
	citation_expected_runs = 0
	required_sections_ok = 0
	expected_task_match = 0
	expected_source_match = 0
	expected_support_match = 0
	unknown_signal_match = 0
	open_questions_presence = 0
	run_errors = 0
	latencies: list[float] = []
	answer_latencies: list[float] = []
	task_coverages: list[float] = []
	source_coverages: list[float] = []
	retrieval_hits: list[int] = []
	failure_catalog: Counter[str] = Counter()

	per_case: list[dict[str, Any]] = []
	for case in cases:
		total_cases += 1
		trial_rows: list[dict[str, Any]] = []
		for trial_index in range(trials_per_case):
			total_runs += 1
			requires_supported = case.expected_supported is not False
			try:
				result = run_planning_workflow(
					goal=case.goal,
					chunks_path=chunks_path,
					metadata_path=metadata_path,
					keyword_index_path=keyword_index_path,
					vector_index_path=vector_index_path,
					config=config,
					llm_client=llm_client,
				)
			except Exception as exc:  # noqa: BLE001
				run_errors += 1
				failure_catalog["run_exception"] += 1
				trial_rows.append(
					{
						"trial_index": trial_index + 1,
						"supported": False,
						"citation_ok": False,
						"required_sections_ok": False,
						"expected_task_match": False,
						"expected_source_match": False,
						"expected_tasks": list(case.expected_tasks),
						"expected_sources": list(case.expected_sources),
						"expected_supported": case.expected_supported,
						"required_unknown_signals": list(case.required_unknown_signals),
						"min_open_questions_count": case.min_open_questions_count,
						"citation_sources": [],
						"retrieval_hit_count": 0,
						"stage_times_ms": {},
						"generation_metadata": {},
						"guardrail_status": {},
						"answer": "",
						"task_coverage_pct": 0.0,
						"source_coverage_pct": 0.0,
						"support_expectation_match": False,
						"unknown_signal_match": False,
						"open_questions_presence_match": False,
						"failure_reasons": ["run_exception"],
						"error": str(exc),
					}
				)
				continue

			answer_text = result.response.answer
			sections_ok = all(f"## {section}" in answer_text for section in REQUIRED_SECTIONS)
			task_ok, task_coverage = _task_match(answer_text, case.expected_tasks, min_task_token_overlap)
			citation_sources = [str(citation.get("source_file", "")) for citation in result.response.citations]
			source_ok, source_coverage = _source_match(citation_sources, case.expected_sources, strict_source_match)
			support_match = _support_expectation_match(result.response.supported, case.expected_supported)
			unknown_ok = _unknown_signal_match(answer_text, case.required_unknown_signals)
			open_questions_ok = _open_questions_presence_match(answer_text, case.min_open_questions_count)
			trial_failure_reasons: list[str] = []

			if result.response.supported:
				raw_supported += 1
			if result.guardrail_status.get("citation_ok"):
				raw_citation_ok += 1

			if requires_supported:
				support_expected_runs += 1
				citation_expected_runs += 1
				if result.response.supported:
					supported_expected_ok += 1
				else:
					trial_failure_reasons.append("unsupported_response")
				if result.guardrail_status.get("citation_ok"):
					citation_expected_ok += 1
				else:
					trial_failure_reasons.append("citation_guardrail_failed")
			elif result.response.supported:
				# If unsupported was expected but we returned supported, record this mismatch explicitly.
				trial_failure_reasons.append("unexpected_supported_response")

			if sections_ok:
				required_sections_ok += 1
			else:
				trial_failure_reasons.append("missing_required_sections")
			if task_ok:
				expected_task_match += 1
			else:
				trial_failure_reasons.append("expected_tasks_not_matched")
			if source_ok:
				expected_source_match += 1
			else:
				trial_failure_reasons.append("expected_sources_not_matched")
			if support_match:
				expected_support_match += 1
			else:
				trial_failure_reasons.append("expected_support_not_matched")
			if unknown_ok:
				unknown_signal_match += 1
			else:
				trial_failure_reasons.append("required_unknown_signals_missing")
			if open_questions_ok:
				open_questions_presence += 1
			else:
				trial_failure_reasons.append("open_questions_presence_not_matched")

			for reason in trial_failure_reasons:
				failure_catalog[reason] += 1

			latencies.append(float(result.stage_times_ms.get("total", 0.0)))
			answer_latencies.append(float(result.stage_times_ms.get("answer_generation", 0.0)))
			task_coverages.append(task_coverage)
			source_coverages.append(source_coverage)
			retrieval_hits.append(len(result.retrieval_hits))

			trial_rows.append(
				{
					"trial_index": trial_index + 1,
					"supported": result.response.supported,
					"citation_ok": result.guardrail_status.get("citation_ok"),
					"required_sections_ok": sections_ok,
					"expected_task_match": task_ok,
					"expected_source_match": source_ok,
					"expected_tasks": list(case.expected_tasks),
					"expected_sources": list(case.expected_sources),
					"expected_supported": case.expected_supported,
					"required_unknown_signals": list(case.required_unknown_signals),
					"min_open_questions_count": case.min_open_questions_count,
					"citation_sources": citation_sources,
					"retrieval_hit_count": len(result.retrieval_hits),
					"stage_times_ms": result.stage_times_ms,
					"generation_metadata": result.generation_metadata,
					"guardrail_status": result.guardrail_status,
					"answer": answer_text,
					"task_coverage_pct": round(task_coverage * 100.0, 3),
					"source_coverage_pct": round(source_coverage * 100.0, 3),
					"support_expectation_match": support_match,
					"unknown_signal_match": unknown_ok,
					"open_questions_presence_match": open_questions_ok,
					"failure_reasons": trial_failure_reasons,
				}
			)

		per_case.append(
			{
				"id": case.id,
				"goal": case.goal,
				"expected_tasks": list(case.expected_tasks),
				"expected_sources": list(case.expected_sources),
				"trials": trial_rows,
				"summary": {
					"supported_rate_pct": round(_percent(sum(1 for row in trial_rows if row["supported"]), trials_per_case), 3),
					"citation_ok_rate_pct": round(_percent(sum(1 for row in trial_rows if row["citation_ok"]), trials_per_case), 3),
					"required_sections_rate_pct": round(_percent(sum(1 for row in trial_rows if row["required_sections_ok"]), trials_per_case), 3),
					"expected_task_match_rate_pct": round(_percent(sum(1 for row in trial_rows if row["expected_task_match"]), trials_per_case), 3),
					"expected_source_match_rate_pct": round(_percent(sum(1 for row in trial_rows if row["expected_source_match"]), trials_per_case), 3),
					"expected_support_match_rate_pct": round(_percent(sum(1 for row in trial_rows if row["support_expectation_match"]), trials_per_case), 3),
					"unknown_signal_match_rate_pct": round(_percent(sum(1 for row in trial_rows if row["unknown_signal_match"]), trials_per_case), 3),
					"open_questions_presence_rate_pct": round(_percent(sum(1 for row in trial_rows if row["open_questions_presence_match"]), trials_per_case), 3),
					"task_coverage_avg_pct": round(_mean([float(row.get("task_coverage_pct", 0.0)) for row in trial_rows]), 3),
					"source_coverage_avg_pct": round(_mean([float(row.get("source_coverage_pct", 0.0)) for row in trial_rows]), 3),
				},
			}
		)

	metrics = {
		"supported_rate_pct": round(_percent(supported_expected_ok, support_expected_runs), 3),
		"citation_ok_rate_pct": round(_percent(citation_expected_ok, citation_expected_runs), 3),
		"raw_supported_rate_pct": round(_percent(raw_supported, total_runs), 3),
		"raw_citation_ok_rate_pct": round(_percent(raw_citation_ok, total_runs), 3),
		"required_sections_rate_pct": round(_percent(required_sections_ok, total_runs), 3),
		"expected_task_match_rate_pct": round(_percent(expected_task_match, total_runs), 3),
		"expected_source_match_rate_pct": round(_percent(expected_source_match, total_runs), 3),
		"expected_support_match_rate_pct": round(_percent(expected_support_match, total_runs), 3),
		"unknown_signal_match_rate_pct": round(_percent(unknown_signal_match, total_runs), 3),
		"open_questions_presence_rate_pct": round(_percent(open_questions_presence, total_runs), 3),
		"run_error_rate_pct": round(_percent(run_errors, total_runs), 3),
		"task_coverage_avg_pct": round(_mean([value * 100.0 for value in task_coverages]), 3),
		"source_coverage_avg_pct": round(_mean([value * 100.0 for value in source_coverages]), 3),
		"retrieval_hits_avg": round(_mean([float(value) for value in retrieval_hits]), 3),
		"latency_p50_ms": round(float(median(latencies)) if latencies else 0.0, 3),
		"latency_p95_ms": round(_p95(latencies), 3),
		"answer_generation_p50_ms": round(float(median(answer_latencies)) if answer_latencies else 0.0, 3),
		"answer_generation_p95_ms": round(_p95(answer_latencies), 3),
	}

	gate_signals = {
		"strict_source_match": strict_source_match,
		"min_task_token_overlap": min_task_token_overlap,
		"gate_ready": (
			total_runs > 0
			and metrics["run_error_rate_pct"] == 0.0
			and metrics["supported_rate_pct"] == 100.0
			and metrics["citation_ok_rate_pct"] == 100.0
			and metrics["required_sections_rate_pct"] == 100.0
			and metrics["expected_task_match_rate_pct"] == 100.0
			and metrics["expected_source_match_rate_pct"] == 100.0
			and metrics["expected_support_match_rate_pct"] == 100.0
			and metrics["unknown_signal_match_rate_pct"] == 100.0
			and metrics["open_questions_presence_rate_pct"] == 100.0
		),
	}

	return {
		"total_cases": total_cases,
		"trials_per_case": trials_per_case,
		"total_runs": total_runs,
		"metrics": metrics,
		"gate_signals": gate_signals,
		"failure_catalog": dict(failure_catalog),
		"per_case": per_case,
	}


def _task_match(text: str, expected: Sequence[str], min_overlap: float) -> tuple[bool, float]:
	if not expected:
		return True, 1.0

	extracted_tasks = _extract_ordered_tasks(text)
	if not extracted_tasks:
		return False, 0.0

	matched = 0
	for expected_task in expected:
		expected_tokens = _expand_task_tokens(_normalize_tokens(expected_task))
		if not expected_tokens:
			matched += 1
			continue
		best_overlap = 0.0
		for candidate in extracted_tasks:
			candidate_tokens = _expand_task_tokens(_normalize_tokens(candidate))
			if not candidate_tokens:
				continue
			overlap = len(expected_tokens.intersection(candidate_tokens)) / float(len(expected_tokens))
			best_overlap = max(best_overlap, overlap)
		if best_overlap >= min_overlap:
			matched += 1

	coverage = matched / float(len(expected))
	# Treat >=2/3 expected-task coverage as a pass to reduce brittle all-or-nothing scoring.
	return coverage >= 0.66, coverage


def _support_expectation_match(actual_supported: bool, expected_supported: bool | None) -> bool:
	if expected_supported is None:
		return True
	return bool(actual_supported) == bool(expected_supported)


def _unknown_signal_match(text: str, required_unknown_signals: Sequence[str]) -> bool:
	if not required_unknown_signals:
		return True
	value = (text or "").lower()
	for signal in required_unknown_signals:
		if str(signal).lower() not in value:
			return False
	return True


def _open_questions_presence_match(text: str, min_open_questions_count: int | None) -> bool:
	if min_open_questions_count is None:
		return True
	open_questions_text = _extract_section_text(text or "", "Open Questions")
	count = _count_action_lines(open_questions_text)
	return count >= max(0, int(min_open_questions_count))


def _extract_section_text(text: str, section_name: str) -> str:
	header = f"## {section_name}"
	if header not in text:
		return ""
	after = text.split(header, 1)[1]
	match = re.search(r"\n##\s+", after)
	if match:
		after = after[: match.start()]
	return after


def _count_action_lines(text: str) -> int:
	count = 0
	for raw_line in (text or "").splitlines():
		line = raw_line.strip()
		if not line:
			continue
		if line.startswith(("-", "*")) or re.match(r"^\d+[\.)]\s+", line):
			count += 1
		elif len(line.split()) > 2:
			count += 1
	return count


def _extract_ordered_tasks(text: str) -> list[str]:
	value = text or ""
	if "## Ordered Tasks" not in value:
		return []
	after_header = value.split("## Ordered Tasks", 1)[1]
	next_section_match = re.search(r"\n##\s+", after_header)
	if next_section_match:
		after_header = after_header[: next_section_match.start()]

	tasks: list[str] = []
	for line in after_header.splitlines():
		line_value = line.strip()
		if not line_value:
			continue
		if re.match(r"^\d+[\.)]\s+", line_value):
			tasks.append(re.sub(r"^\d+[\.)]\s+", "", line_value).strip())
	return tasks


def _normalize_tokens(value: str) -> set[str]:
	stop_words = {
		"the",
		"and",
		"for",
		"with",
		"from",
		"that",
		"this",
		"then",
		"into",
		"across",
		"using",
		"safe",
		"safely",
		"change",
		"current",
		"steps",
		"step",
		"plan",
	}
	return {
		token
		for token in re.findall(r"[a-z0-9]+", (value or "").lower())
		if len(token) > 1 and token not in stop_words
	}


def _expand_task_tokens(tokens: set[str]) -> set[str]:
	if not tokens:
		return set()

	aliases: dict[str, set[str]] = {
		"identify": {"identify", "assess", "determine", "discover", "inventory"},
		"validate": {"validate", "verify", "confirm", "check"},
		"execute": {"execute", "run", "apply", "perform", "restart", "rollout"},
		"monitor": {"monitor", "observe", "watch", "track"},
		"prerequisites": {"prerequisite", "prerequisites", "requirements", "precheck", "prechecks"},
		"access": {"access", "authorization", "auth", "permission", "permissions", "credentials", "roles"},
		"systems": {"system", "systems", "host", "hosts", "node", "nodes", "environment", "environments"},
		"disk": {"disk", "storage", "filesystem", "capacity", "pressure", "usage", "df", "du"},
		"cleanup": {"cleanup", "clean", "purge", "retention", "logrotate", "journalctl"},
		"log": {"log", "logs", "logging"},
	}

	expanded = set(tokens)
	for token in list(tokens):
		for group in aliases.values():
			if token in group:
				expanded.update(group)
	return expanded


def _source_match(paths: Sequence[str], expected_substrings: Sequence[str], strict_match: bool) -> tuple[bool, float]:
	if not expected_substrings:
		return True, 1.0

	normalized_paths = [value.lower() for value in paths]
	matched = 0
	for expected in expected_substrings:
		expected_lower = str(expected).lower()
		if any(expected_lower in value for value in normalized_paths):
			matched += 1

	coverage = matched / float(len(expected_substrings))
	if strict_match:
		return coverage == 1.0, coverage
	return matched > 0, coverage


def _percent(num: int, den: int) -> float:
	return (num / den * 100.0) if den else 0.0


def _mean(values: list[float]) -> float:
	if not values:
		return 0.0
	return sum(values) / float(len(values))


def _p95(values: list[float]) -> float:
	if not values:
		return 0.0
	sorted_vals = sorted(values)
	idx = min(len(sorted_vals) - 1, int(round(0.95 * (len(sorted_vals) - 1))))
	return float(sorted_vals[idx])