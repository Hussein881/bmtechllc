"""Tool: test_phase4

Tag: reusable-asset

What this tool does:
- Runs a one-command Phase 4 test flow.
- Executes planner unit tests, a live planner smoke test, and planner eval.
- Produces a pass/fail summary and exits non-zero on failed checks.

Inputs:
- Optional Watsonx overrides (project/url/model/apikey).
- Planner smoke-test goal.
- Eval trials and metric thresholds.

Outputs:
- Console summary with step-level status and key metrics.
- Optional JSON summary payload.

Status:
- Phase 4 testing utility.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Run one-command Phase 4 planner verification.")
	parser.add_argument(
		"--goal",
		default="Plan a safe rollout for investigating log growth and reducing disk pressure on Linux.",
		help="Goal used for planner smoke test",
	)
	parser.add_argument("--trials", type=int, default=2, help="Trials per eval case")
	parser.add_argument("--report-out", type=Path, default=Path("data/eval/plan_report_latest.json"))
	parser.add_argument("--skip-live", action="store_true", help="Skip live planner smoke + eval steps")
	parser.add_argument("--project-id", default="", help="Override DEBUG_AGENT_LLM_WATSONX_PROJECT_ID")
	parser.add_argument("--url", default="", help="Override DEBUG_AGENT_LLM_WATSONX_URL")
	parser.add_argument("--apikey-file", default="", help="Override DEBUG_AGENT_LLM_WATSONX_APIKEY_FILE")
	parser.add_argument("--iam-token-url", default="", help="Override DEBUG_AGENT_LLM_IAM_TOKEN_URL")
	parser.add_argument("--model-id", default="", help="Override WKA_WATSONX_MODEL_ID")
	parser.add_argument("--api-version", default="", help="Override WKA_WATSONX_API_VERSION")
	parser.add_argument("--prompt-version", default="", help="Override WKA_WATSONX_PROMPT_VERSION")
	parser.add_argument("--min-supported-rate", type=float, default=100.0)
	parser.add_argument("--min-citation-rate", type=float, default=100.0)
	parser.add_argument("--min-required-sections-rate", type=float, default=100.0)
	parser.add_argument("--min-source-match-rate", type=float, default=100.0)
	parser.add_argument(
		"--min-task-match-rate",
		type=float,
		default=60.0,
		help="Minimum expected task match rate. Higher default is intentional to surface planning gaps.",
	)
	parser.add_argument("--json", action="store_true", help="Emit machine-readable final summary")
	return parser.parse_args()


def _build_env(args: argparse.Namespace) -> dict[str, str]:
	env = os.environ.copy()
	env["PYTHONPATH"] = f"src{os.pathsep}{env.get('PYTHONPATH', '')}".rstrip(os.pathsep)

	if args.project_id.strip():
		env["DEBUG_AGENT_LLM_WATSONX_PROJECT_ID"] = args.project_id.strip()
	if args.url.strip():
		env["DEBUG_AGENT_LLM_WATSONX_URL"] = args.url.strip()
	if args.apikey_file.strip():
		env["DEBUG_AGENT_LLM_WATSONX_APIKEY_FILE"] = args.apikey_file.strip()
	if args.iam_token_url.strip():
		env["DEBUG_AGENT_LLM_IAM_TOKEN_URL"] = args.iam_token_url.strip()
	if args.model_id.strip():
		env["WKA_WATSONX_MODEL_ID"] = args.model_id.strip()
	if args.api_version.strip():
		env["WKA_WATSONX_API_VERSION"] = args.api_version.strip()
	if args.prompt_version.strip():
		env["WKA_WATSONX_PROMPT_VERSION"] = args.prompt_version.strip()

	return env


def _run_command(command: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
	return subprocess.run(command, env=env, text=True, capture_output=True, check=False)


def _print_step(name: str, passed: bool, detail: str = "") -> None:
	status = "PASS" if passed else "FAIL"
	print(f"[{status}] {name}")
	if detail:
		print(detail)


def main() -> None:
	args = parse_args()
	env = _build_env(args)
	summary: dict[str, Any] = {
		"unit_tests": {"passed": False},
		"smoke": {"passed": False, "skipped": bool(args.skip_live)},
		"eval": {"passed": False, "skipped": bool(args.skip_live)},
		"overall_passed": False,
	}

	root_dir = Path(__file__).resolve().parents[1]
	os.chdir(root_dir)

	# Step 1: unit tests
	unit_cmd = [
		sys.executable,
		"-m",
		"unittest",
		"tests.unit.test_phase4_planning_workflow",
		"tests.unit.test_phase4_planning_eval",
		"-v",
	]
	unit_result = _run_command(unit_cmd, env)
	unit_passed = unit_result.returncode == 0
	summary["unit_tests"] = {
		"passed": unit_passed,
		"command": unit_cmd,
		"stdout": unit_result.stdout,
		"stderr": unit_result.stderr,
	}
	_print_step("Phase 4 unit tests", unit_passed)
	if not unit_passed:
		print(unit_result.stdout)
		print(unit_result.stderr)

	if args.skip_live:
		overall = unit_passed
		summary["overall_passed"] = overall
		if args.json:
			print(json.dumps(summary, ensure_ascii=True, indent=2))
		else:
			_print_step("Overall Phase 4 test run", overall, "Live steps skipped via --skip-live")
		raise SystemExit(0 if overall else 1)

	# Step 2: live smoke test
	smoke_cmd = [
		sys.executable,
		"scripts/generate_plan.py",
		args.goal,
		"--json",
	]
	smoke_result = _run_command(smoke_cmd, env)
	smoke_payload: dict[str, Any] = {}
	smoke_passed = False
	if smoke_result.returncode == 0:
		try:
			smoke_payload = json.loads(smoke_result.stdout)
			supported = bool(smoke_payload.get("supported"))
			citation_ok = bool((smoke_payload.get("guardrail_status") or {}).get("citation_ok"))
			has_citations = bool(smoke_payload.get("citations"))
			smoke_passed = supported and citation_ok and has_citations
		except json.JSONDecodeError:
			smoke_passed = False

	summary["smoke"] = {
		"passed": smoke_passed,
		"command": smoke_cmd,
		"stdout": smoke_result.stdout,
		"stderr": smoke_result.stderr,
		"payload": smoke_payload,
	}
	_print_step("Phase 4 live smoke test", smoke_passed)
	if not smoke_passed:
		print(smoke_result.stdout)
		print(smoke_result.stderr)

	# Step 3: planner eval run
	eval_cmd = [
		sys.executable,
		"scripts/run_plan_eval.py",
		"--trials",
		str(max(1, args.trials)),
		"--report-out",
		str(args.report_out),
		"--min-task-token-overlap",
		"0.60",
	]
	eval_result = _run_command(eval_cmd, env)
	report_payload: dict[str, Any] = {}
	eval_passed = False
	eval_detail = ""
	if eval_result.returncode == 0 and args.report_out.exists():
		try:
			report_payload = json.loads(args.report_out.read_text(encoding="utf-8"))
			metrics = report_payload.get("metrics", {})
			checks = {
				"supported_rate_pct": float(metrics.get("supported_rate_pct", 0.0)) >= args.min_supported_rate,
				"citation_ok_rate_pct": float(metrics.get("citation_ok_rate_pct", 0.0)) >= args.min_citation_rate,
				"required_sections_rate_pct": float(metrics.get("required_sections_rate_pct", 0.0)) >= args.min_required_sections_rate,
				"expected_source_match_rate_pct": float(metrics.get("expected_source_match_rate_pct", 0.0)) >= args.min_source_match_rate,
				"expected_task_match_rate_pct": float(metrics.get("expected_task_match_rate_pct", 0.0)) >= args.min_task_match_rate,
			}
			eval_passed = all(checks.values())
			failed = [name for name, passed in checks.items() if not passed]
			eval_detail = "All metric thresholds passed" if not failed else f"Threshold failures: {', '.join(failed)}"
		except json.JSONDecodeError:
			eval_passed = False
			eval_detail = "Could not parse eval report JSON"
	else:
		eval_detail = "Eval command failed or report file missing"

	summary["eval"] = {
		"passed": eval_passed,
		"command": eval_cmd,
		"stdout": eval_result.stdout,
		"stderr": eval_result.stderr,
		"report_path": str(args.report_out),
		"report": report_payload,
		"detail": eval_detail,
		"thresholds": {
			"min_supported_rate": args.min_supported_rate,
			"min_citation_rate": args.min_citation_rate,
			"min_required_sections_rate": args.min_required_sections_rate,
			"min_source_match_rate": args.min_source_match_rate,
			"min_task_match_rate": args.min_task_match_rate,
		},
	}
	_print_step("Phase 4 eval suite", eval_passed, eval_detail)
	if report_payload:
		metrics = report_payload.get("metrics", {})
		print(
			"metrics="
			+ json.dumps(
				{
					"supported_rate_pct": metrics.get("supported_rate_pct"),
					"citation_ok_rate_pct": metrics.get("citation_ok_rate_pct"),
					"required_sections_rate_pct": metrics.get("required_sections_rate_pct"),
					"expected_task_match_rate_pct": metrics.get("expected_task_match_rate_pct"),
					"expected_source_match_rate_pct": metrics.get("expected_source_match_rate_pct"),
					"latency_p50_ms": metrics.get("latency_p50_ms"),
					"latency_p95_ms": metrics.get("latency_p95_ms"),
				},
				ensure_ascii=True,
			)
		)
	if not eval_passed:
		print(eval_result.stdout)
		print(eval_result.stderr)

	overall = unit_passed and smoke_passed and eval_passed
	summary["overall_passed"] = overall

	if args.json:
		print(json.dumps(summary, ensure_ascii=True, indent=2))
	else:
		_print_step("Overall Phase 4 test run", overall)

	raise SystemExit(0 if overall else 1)


if __name__ == "__main__":
	main()
