"""Tool: run_phase6_readiness

Tag: reusable-asset

What this tool does:
- Builds a Phase 6 readiness report from existing evaluation artifacts.
- Optionally runs ingestion/index observability commands and captures stage timings.
- Produces an index-evolution recommendation (incremental vs full rebuild) from thresholds.

Inputs:
- Existing eval reports in data/eval.
- Optional live observability run of ingest_docs.py and build_indexes.py.

Outputs:
- data/eval/phase6_readiness_latest.json (or user-provided path).
- Console summary for gate and trend review.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Run Phase 6 readiness aggregation.")
	parser.add_argument("--run-observability", action="store_true", help="Run ingestion/index commands and capture stage timing metrics")
	parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
	parser.add_argument("--chunks", type=Path, default=Path("data/processed/chunks.jsonl"))
	parser.add_argument("--metadata", type=Path, default=Path("data/processed/metadata.parquet"))
	parser.add_argument("--quarantine", type=Path, default=Path("data/processed/quarantine.jsonl"))
	parser.add_argument("--manifest", type=Path, default=Path("data/processed/manifest.sqlite"))
	parser.add_argument("--keyword-dir", type=Path, default=Path("data/indexes/keyword"))
	parser.add_argument("--vector-dir", type=Path, default=Path("data/indexes/vector"))
	parser.add_argument("--qa-report", type=Path, default=Path("data/eval/report_latest.json"))
	parser.add_argument("--howto-report", type=Path, default=Path("data/eval/howto_report_latest.json"))
	parser.add_argument("--plan-report", type=Path, default=Path("data/eval/plan_report_latest.json"))
	parser.add_argument("--curation-report", type=Path, default=Path("data/eval/curation_report_latest.json"))
	parser.add_argument("--corpus-quality-report", type=Path, default=Path("data/eval/corpus_quality_report_latest.json"))
	parser.add_argument("--llm-report", type=Path, default=Path("data/eval/llm_report_latest.json"))
	parser.add_argument("--triage-history", type=Path, default=Path("data/eval/curation_triage_history.jsonl"))
	parser.add_argument("--execution-log", type=Path, default=Path("project_memory/04_EXECUTION.md"))
	parser.add_argument("--api-base-url", default="", help="Optional API base URL for interface parity checks (for example http://127.0.0.1:8770)")
	parser.add_argument("--full-rebuild-warning-ms", type=float, default=120000.0)
	parser.add_argument("--full-rebuild-warning-chunks", type=int, default=50000)
	parser.add_argument("--report-out", type=Path, default=Path("data/eval/phase6_readiness_latest.json"))
	parser.add_argument("--markdown-out", type=Path, default=Path("data/eval/phase6_readiness_packet.md"))
	return parser.parse_args()


def _load_json(path: Path) -> dict[str, Any]:
	if not path.exists():
		return {}
	text = path.read_text(encoding="utf-8").strip()
	if not text:
		return {}
	try:
		payload = json.loads(text)
		if isinstance(payload, dict):
			return payload
	except json.JSONDecodeError:
		return {}
	return {}


def _parse_key_values(output: str) -> dict[str, Any]:
	parsed: dict[str, Any] = {}
	for raw_line in output.splitlines():
		line = raw_line.strip()
		if not line or "=" not in line:
			continue
		key, value = line.split("=", 1)
		key = key.strip()
		value = value.strip()
		if not key:
			continue
		parsed[key] = value
	for key, value in list(parsed.items()):
		if not isinstance(value, str):
			continue
		try:
			if value.isdigit():
				parsed[key] = int(value)
				continue
			parsed[key] = float(value)
		except ValueError:
			continue
	return parsed


def _run_command(command: list[str]) -> dict[str, Any]:
	result = subprocess.run(command, capture_output=True, text=True, check=False)
	stdout = result.stdout or ""
	stderr = result.stderr or ""
	return {
		"command": command,
		"exit_code": result.returncode,
		"stdout": stdout,
		"stderr": stderr,
		"parsed": _parse_key_values(stdout),
	}


def _count_chunk_rows(path: Path) -> int:
	if not path.exists():
		return 0
	count = 0
	with path.open("r", encoding="utf-8") as handle:
		for line in handle:
			if line.strip():
				count += 1
	return count


def _generation_telemetry_summary(report: dict[str, Any]) -> dict[str, Any]:
	total_runs = int(report.get("total_runs", 0) or 0)
	if total_runs <= 0:
		return {
			"total_runs": 0,
			"runs_with_generation_metadata": 0,
			"coverage_pct": 0.0,
			"runs_with_token_counts": 0,
			"token_coverage_pct": 0.0,
		}

	runs_with_generation_metadata = 0
	runs_with_token_counts = 0

	for case in report.get("per_case", []):
		if not isinstance(case, dict):
			continue
		for trial in case.get("trials", []):
			if not isinstance(trial, dict):
				continue
			metadata = trial.get("generation_metadata")
			if isinstance(metadata, dict) and metadata:
				runs_with_generation_metadata += 1
				if metadata.get("input_token_count") is not None and metadata.get("output_token_count") is not None:
					runs_with_token_counts += 1

	coverage_pct = (runs_with_generation_metadata / total_runs * 100.0) if total_runs else 0.0
	token_coverage_pct = (runs_with_token_counts / total_runs * 100.0) if total_runs else 0.0
	return {
		"total_runs": total_runs,
		"runs_with_generation_metadata": runs_with_generation_metadata,
		"coverage_pct": round(coverage_pct, 3),
		"runs_with_token_counts": runs_with_token_counts,
		"token_coverage_pct": round(token_coverage_pct, 3),
	}


def _compute_run_error_rate(report: dict[str, Any]) -> float:
	total_runs = int(report.get("total_runs", 0) or 0)
	if total_runs <= 0:
		return 0.0
	error_runs = 0
	for case in report.get("per_case", []):
		if not isinstance(case, dict):
			continue
		for trial in case.get("trials", []):
			if not isinstance(trial, dict):
				continue
			if str(trial.get("error", "")).strip():
				error_runs += 1
	return round((error_runs / total_runs) * 100.0, 3)


def _compute_spot_audit_metrics(history_path: Path) -> dict[str, Any]:
	if not history_path.exists():
		return {
			"history_found": False,
			"accepted_decision_events": 0,
			"rollback_events": 0,
			"spot_audit_disagreement_rate_pct": 0.0,
		}

	accepted_decision_events = 0
	rollback_events = 0
	triage_snapshot_events = 0

	with history_path.open("r", encoding="utf-8") as handle:
		for line in handle:
			line = line.strip()
			if not line:
				continue
			try:
				event = json.loads(line)
			except json.JSONDecodeError:
				continue
			if not isinstance(event, dict):
				continue
			event_type = str(event.get("event_type", "")).strip().lower()
			if event_type == "rollback":
				rollback_events += 1
			elif event_type == "triage_snapshot":
				triage_snapshot_events += 1
				summary = event.get("triage_summary")
				if isinstance(summary, dict):
					accepted_decision_events += int(summary.get("accepted_count", 0) or 0)

	disagreement_rate = (rollback_events / accepted_decision_events * 100.0) if accepted_decision_events else 0.0
	return {
		"history_found": True,
		"triage_snapshot_events": triage_snapshot_events,
		"accepted_decision_events": accepted_decision_events,
		"rollback_events": rollback_events,
		"metric_non_vacuous": bool(accepted_decision_events > 0 and rollback_events > 0),
		"spot_audit_disagreement_rate_pct": round(disagreement_rate, 3),
	}


def _extract_open_conditions(execution_log_path: Path) -> dict[str, Any]:
	if not execution_log_path.exists():
		return {
			"source_found": False,
			"open_conditions": [],
			"open_condition_count": 0,
		}

	lines = execution_log_path.read_text(encoding="utf-8").splitlines()
	open_conditions: list[dict[str, Any]] = []

	idx = 0
	while idx < len(lines):
		line = lines[idx].strip()
		if not (line.startswith("### Gate ") and "Sign-Off" in line):
			idx += 1
			continue

		gate_name = line.replace("### ", "").replace(" Sign-Off", "").strip()
		block_lines: list[str] = []
		idx += 1
		while idx < len(lines):
			next_line = lines[idx].strip()
			if next_line.startswith("### "):
				break
			block_lines.append(next_line)
			idx += 1

		decision = ""
		conditions: list[str] = []
		in_conditions = False

		for block_line in block_lines:
			if block_line.startswith("- Decision:"):
				decision = block_line.split(":", 1)[1].strip().lower()
				in_conditions = False
				continue

			if block_line.startswith("- Conditions:"):
				inline_value = block_line.split(":", 1)[1].strip()
				if inline_value and inline_value.lower() != "none":
					conditions.append(inline_value)
				in_conditions = True
				continue

			if block_line.startswith("- Notes:"):
				in_conditions = False
				continue

			if in_conditions and block_line.startswith("-"):
				value = block_line.lstrip("-").strip()
				if value and value.lower() != "none":
					conditions.append(value)

		if decision == "approved-with-conditions" and conditions:
			open_conditions.append(
				{
					"gate": gate_name,
					"decision": decision,
					"conditions": conditions,
				}
			)

	return {
		"source_found": True,
		"open_conditions": open_conditions,
		"open_condition_count": len(open_conditions),
	}


def _howto_eval_provenance(howto_report: dict[str, Any]) -> dict[str, Any]:
	golden = howto_report.get("golden_integrity") if isinstance(howto_report, dict) else {}
	if not isinstance(golden, dict):
		golden = {}
	return {
		"trials_per_case": int(howto_report.get("trials_per_case", 0) or 0),
		"dataset_path": str(golden.get("dataset_path", "")),
		"review_status": str(golden.get("review_status", "unknown") or "unknown"),
		"gate_eligible": bool(golden.get("gate_eligible", False)),
		"hash_match": bool(golden.get("hash_match", False)) if golden else False,
	}


def _verify_interface_parity(api_base_url: str, report_path: Path) -> dict[str, Any]:
	if not api_base_url.strip():
		return {
			"checked": False,
			"status": "not_requested",
			"health_ok": False,
			"readiness_keys_match": False,
		}

	base = api_base_url.rstrip("/")
	health_ok = False
	keys_match = False
	error_message = ""

	try:
		with urllib.request.urlopen(f"{base}/health", timeout=10) as response:
			health_payload = json.loads(response.read().decode("utf-8"))
		health_ok = isinstance(health_payload, dict) and health_payload.get("status") == "ok"

		with urllib.request.urlopen(f"{base}/phase6/readiness", timeout=10) as response:
			api_readiness_payload = json.loads(response.read().decode("utf-8"))

		local_payload = _load_json(report_path)
		if isinstance(api_readiness_payload, dict) and isinstance(local_payload, dict):
			keys_match = set(api_readiness_payload.keys()) == set(local_payload.keys())
	except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as exc:
		error_message = str(exc)

	status = "ok" if (health_ok and keys_match) else "failed"
	return {
		"checked": True,
		"status": status,
		"health_ok": health_ok,
		"readiness_keys_match": keys_match,
		"error": error_message,
	}


def _write_markdown_packet(path: Path, report: dict[str, Any]) -> None:
	quality = report.get("quality_metrics", {})
	readiness = report.get("gate6_readiness_signals", {})
	index_rec = report.get("index_evolution_recommendation", {})
	spot_audit = report.get("curation_spot_audit", {})
	carry_forward = report.get("carry_forward_conditions", {})
	howto_eval_meta = report.get("howto_eval_provenance", {})
	parity = report.get("interface_parity", {})

	qa_refusal = readiness.get("qa_refusal_accuracy_pct", 0.0)
	howto_error_rate = readiness.get("howto_run_error_rate_pct", 0.0)
	planner_gate_ready = readiness.get("planner_gate_ready", False)
	metrics_present = readiness.get("baseline_quality_metrics_present", False)
	reports_present = readiness.get("fixed_eval_reports_present", False)
	open_condition_count = int(carry_forward.get("open_condition_count", 0) or 0)

	gate6_ready = bool(
		reports_present
		and metrics_present
		and planner_gate_ready
		and qa_refusal >= 90.0
		and howto_error_rate <= 10.0
		and open_condition_count == 0
	)

	lines = [
		"# Gate 6 Readiness Packet",
		"",
		f"Generated at: {report.get('generated_at', '')}",
		"",
		"## Summary",
		f"- Gate 6 ready: {'yes' if gate6_ready else 'no'}",
		f"- Open carried conditions count: {open_condition_count}",
		f"- Index strategy recommendation: {index_rec.get('decision', 'unknown')}",
		f"- Recommendation reason: {index_rec.get('reason', 'unknown')}",
		"",
		"## Quality Snapshot",
		f"- QA refusal accuracy (%): {readiness.get('qa_refusal_accuracy_pct', 0.0)}",
		f"- How-To run error rate (%): {readiness.get('howto_run_error_rate_pct', 0.0)}",
		f"- Planner gate-ready flag: {planner_gate_ready}",
		f"- Baseline quality metrics present: {metrics_present}",
		"",
		"## Curation Governance Snapshot",
		f"- Spot-audit disagreement rate (%): {spot_audit.get('spot_audit_disagreement_rate_pct', 0.0)}",
		f"- Accepted decision events: {spot_audit.get('accepted_decision_events', 0)}",
		f"- Rollback events: {spot_audit.get('rollback_events', 0)}",
		"",
		"## Observability Snapshot",
		f"- Corpus total chunks: {index_rec.get('observed_total_chunks', 0)}",
		f"- Index build stage_total_ms: {index_rec.get('observed_index_stage_total_ms', 'n/a')}",
		f"- Triggered by time threshold: {index_rec.get('triggered_by_time', False)}",
		f"- Triggered by size threshold: {index_rec.get('triggered_by_size', False)}",
		f"- Full rebuild warning ms: {index_rec.get('full_rebuild_warning_ms', 0.0)}",
		f"- Full rebuild warning chunks: {index_rec.get('full_rebuild_warning_chunks', 0)}",
		"",
		"## How-To Eval Provenance",
		f"- Trials per case: {howto_eval_meta.get('trials_per_case', 0)}",
		f"- Dataset path: {howto_eval_meta.get('dataset_path', '')}",
		f"- Review status: {howto_eval_meta.get('review_status', 'unknown')}",
		f"- Gate eligible: {howto_eval_meta.get('gate_eligible', False)}",
		f"- Hash match: {howto_eval_meta.get('hash_match', False)}",
		"",
		"## Interface Parity",
		f"- Checked: {parity.get('checked', False)}",
		f"- Status: {parity.get('status', 'unknown')}",
		f"- Health endpoint OK: {parity.get('health_ok', False)}",
		f"- Readiness key parity: {parity.get('readiness_keys_match', False)}",
		"",
		"## Source Artifacts",
	]

	sources = report.get("sources", {})
	if isinstance(sources, dict):
		for key, value in sources.items():
			lines.append(f"- {key}: {value}")

	if open_condition_count > 0:
		lines.extend([
			"",
			"## Carry-Forward Conditions",
		])
		for item in carry_forward.get("open_conditions", []):
			if not isinstance(item, dict):
				continue
			gate = str(item.get("gate", "unknown"))
			lines.append(f"- {gate}")
			for condition in item.get("conditions", []):
				lines.append(f"  - {condition}")

	lines.extend([
		"",
		"## Reviewer Sign-Off",
		"- Gate: Gate 6 (Evaluation + Interface)",
		"- Reviewer:",
		"- Date:",
		"- Quality verdict: pass | conditional | fail",
		"- Performance verdict: pass | conditional | fail",
		"- Decision: approved | approved-with-conditions | rejected",
		"- Conditions:",
		"- Notes:",
	])

	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
	args = parse_args()

	qa_report = _load_json(args.qa_report)
	howto_report = _load_json(args.howto_report)
	plan_report = _load_json(args.plan_report)
	curation_report = _load_json(args.curation_report)
	corpus_quality_report = _load_json(args.corpus_quality_report)
	llm_report = _load_json(args.llm_report)
	carry_forward_conditions = _extract_open_conditions(args.execution_log)

	observability: dict[str, Any] = {
		"enabled": bool(args.run_observability),
		"ingestion": {},
		"index_build": {},
	}

	if args.run_observability:
		ingest_command = [
			sys.executable,
			"scripts/ingest_docs.py",
			"--raw-dir",
			str(args.raw_dir),
			"--chunks-output",
			str(args.chunks),
			"--metadata-output",
			str(args.metadata),
			"--quarantine-output",
			str(args.quarantine),
			"--manifest-path",
			str(args.manifest),
		]
		index_command = [
			sys.executable,
			"scripts/build_indexes.py",
			"--chunks",
			str(args.chunks),
			"--keyword-dir",
			str(args.keyword_dir),
			"--vector-dir",
			str(args.vector_dir),
		]
		observability["ingestion"] = _run_command(ingest_command)
		observability["index_build"] = _run_command(index_command)

	index_stage_total_ms = None
	index_build_data = observability.get("index_build", {})
	if isinstance(index_build_data, dict):
		parsed = index_build_data.get("parsed", {})
		if isinstance(parsed, dict):
			value = parsed.get("stage_total_ms")
			if isinstance(value, (int, float)):
				index_stage_total_ms = float(value)

	corpus_total_chunks = int(corpus_quality_report.get("total_chunks", 0) or 0)
	if corpus_total_chunks <= 0:
		corpus_total_chunks = _count_chunk_rows(args.chunks)

	trigger_by_time = bool(index_stage_total_ms is not None and index_stage_total_ms > args.full_rebuild_warning_ms)
	trigger_by_size = bool(corpus_total_chunks > args.full_rebuild_warning_chunks)

	if trigger_by_time or trigger_by_size:
		recommendation = "consider_incremental_index_evolution"
		reason = "warning_threshold_exceeded"
	else:
		recommendation = "keep_full_rebuild_strategy"
		reason = "within_warning_thresholds"

	if args.run_observability:
		ingestion_exit = int(observability.get("ingestion", {}).get("exit_code", 1))
		index_exit = int(observability.get("index_build", {}).get("exit_code", 1))
		if ingestion_exit != 0 or index_exit != 0:
			recommendation = "investigate_observability_failures"
			reason = "ingestion_or_index_command_failed"

	plan_metrics = plan_report.get("metrics", {}) if isinstance(plan_report, dict) else {}
	howto_metrics = howto_report.get("metrics", {}) if isinstance(howto_report, dict) else {}
	howto_run_error_rate = _compute_run_error_rate(howto_report)
	howto_eval_provenance = _howto_eval_provenance(howto_report)
	qa_metrics = qa_report.get("metrics", {}) if isinstance(qa_report, dict) else {}
	curation_metrics = curation_report.get("metrics", {}) if isinstance(curation_report, dict) else {}
	spot_audit_metrics = _compute_spot_audit_metrics(args.triage_history)

	report = {
		"generated_at": datetime.now(tz=timezone.utc).isoformat(),
		"phase": "phase6_evaluation_interface",
		"sources": {
			"qa_report": str(args.qa_report),
			"howto_report": str(args.howto_report),
			"plan_report": str(args.plan_report),
			"curation_report": str(args.curation_report),
			"corpus_quality_report": str(args.corpus_quality_report),
			"llm_report": str(args.llm_report),
		},
		"quality_metrics": {
			"qa": qa_metrics,
			"howto": howto_metrics,
			"planner": plan_metrics,
			"curation": curation_metrics,
			"llm": llm_report.get("metrics", {}) if isinstance(llm_report, dict) else {},
		},
		"generation_telemetry": {
			"howto": _generation_telemetry_summary(howto_report),
			"planner": _generation_telemetry_summary(plan_report),
		},
		"howto_eval_provenance": howto_eval_provenance,
		"observability": observability,
		"carry_forward_conditions": carry_forward_conditions,
		"index_evolution_recommendation": {
			"decision": recommendation,
			"reason": reason,
			"full_rebuild_warning_ms": args.full_rebuild_warning_ms,
			"full_rebuild_warning_chunks": args.full_rebuild_warning_chunks,
			"observed_index_stage_total_ms": round(index_stage_total_ms, 3) if isinstance(index_stage_total_ms, float) else None,
			"observed_total_chunks": corpus_total_chunks,
			"triggered_by_time": trigger_by_time,
			"triggered_by_size": trigger_by_size,
		},
		"curation_spot_audit": spot_audit_metrics,
		"gate6_readiness_signals": {
			"fixed_eval_reports_present": bool(qa_report and plan_report and curation_report),
			"baseline_quality_metrics_present": bool(qa_metrics and plan_metrics and curation_metrics),
			"planner_gate_ready": bool(plan_report.get("gate_signals", {}).get("gate_ready")) if isinstance(plan_report, dict) else False,
			"howto_run_error_rate_pct": howto_run_error_rate,
			"qa_refusal_accuracy_pct": float(qa_metrics.get("refusal_accuracy_pct", 0.0) or 0.0),
			"open_condition_count": int(carry_forward_conditions.get("open_condition_count", 0) or 0),
		},
	}

	args.report_out.parent.mkdir(parents=True, exist_ok=True)
	report["interface_parity"] = _verify_interface_parity(args.api_base_url, args.report_out)
	args.report_out.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
	_write_markdown_packet(args.markdown_out, report)

	print("Phase 6 readiness report complete")
	print(f"report_path={args.report_out}")
	print(f"markdown_packet_path={args.markdown_out}")
	print(f"recommendation={report['index_evolution_recommendation']['decision']}")
	print(f"reason={report['index_evolution_recommendation']['reason']}")
	print(f"observed_total_chunks={report['index_evolution_recommendation']['observed_total_chunks']}")
	print(f"observed_index_stage_total_ms={report['index_evolution_recommendation']['observed_index_stage_total_ms']}")
	print(f"spot_audit_disagreement_rate_pct={spot_audit_metrics['spot_audit_disagreement_rate_pct']}")
	print(f"open_condition_count={carry_forward_conditions['open_condition_count']}")


if __name__ == "__main__":
	main()