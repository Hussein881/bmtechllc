"""Unified CLI interface for evaluation and readiness operations.

Phase 6 intent:
- Provide one command surface to run fixed eval harnesses.
- Keep report generation paths consistent across operators.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _run_command(command: list[str]) -> int:
	completed = subprocess.run(command, check=False)
	return int(completed.returncode)


def _script_path(name: str) -> str:
	project_root = Path(__file__).resolve().parents[3]
	return str(project_root / "scripts" / name)


def _build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description="Work Knowledge Agent unified interface CLI")
	subparsers = parser.add_subparsers(dest="command")

	subparsers.add_parser("qa-eval", help="Run Phase 2 QA evaluation")
	subparsers.add_parser("howto-eval", help="Run Phase 3 How-To evaluation")
	subparsers.add_parser("plan-eval", help="Run Phase 4 planner evaluation")
	subparsers.add_parser("curation-eval", help="Run Phase 5 curation evaluation")
	subparsers.add_parser("llm-eval", help="Run provider-path LLM evaluation")
	subparsers.add_parser("phase6-readiness", help="Run Phase 6 readiness aggregation")

	all_evals = subparsers.add_parser("all-evals", help="Run all major eval harnesses in sequence")
	all_evals.add_argument("--skip-howto", action="store_true", help="Skip How-To evaluation")
	all_evals.add_argument("--skip-plan", action="store_true", help="Skip planner evaluation")
	all_evals.add_argument("--skip-curation", action="store_true", help="Skip curation evaluation")
	all_evals.add_argument("--skip-llm", action="store_true", help="Skip provider-path LLM evaluation")
	all_evals.add_argument("--with-observability", action="store_true", help="Include ingestion/index observability in readiness run")

	return parser


def main(argv: list[str] | None = None) -> int:
	parser = _build_parser()
	args, passthrough = parser.parse_known_args(argv)

	if not args.command:
		parser.print_help()
		return 1

	python_exec = sys.executable

	if args.command == "qa-eval":
		return _run_command([python_exec, _script_path("run_eval.py"), *passthrough])

	if args.command == "howto-eval":
		return _run_command([python_exec, _script_path("run_howto_eval.py"), *passthrough])

	if args.command == "plan-eval":
		return _run_command([python_exec, _script_path("run_plan_eval.py"), *passthrough])

	if args.command == "curation-eval":
		return _run_command([python_exec, _script_path("run_curation_eval.py"), *passthrough])

	if args.command == "llm-eval":
		return _run_command([python_exec, _script_path("run_llm_eval.py"), *passthrough])

	if args.command == "phase6-readiness":
		return _run_command([python_exec, _script_path("run_phase6_readiness.py"), *passthrough])

	if args.command == "all-evals":
		commands: list[list[str]] = []
		commands.append([python_exec, _script_path("run_eval.py"), "--report-out", "data/eval/report_latest.json"])
		if not args.skip_howto:
			commands.append([
				python_exec,
				_script_path("run_howto_eval.py"),
				"--allow-unreviewed-golden",
				"--report-out",
				"data/eval/howto_report_latest.json",
			])
		if not args.skip_plan:
			commands.append([
				python_exec,
				_script_path("run_plan_eval.py"),
				"--allow-unreviewed-golden",
				"--report-out",
				"data/eval/plan_report_latest.json",
			])
		if not args.skip_curation:
			commands.append([python_exec, _script_path("run_curation_eval.py"), "--report-out", "data/eval/curation_report_latest.json"])
		if not args.skip_llm:
			commands.append([python_exec, _script_path("run_llm_eval.py"), "--report-out", "data/eval/llm_report_latest.json"])

		readiness_cmd = [
			python_exec,
			_script_path("run_phase6_readiness.py"),
			"--report-out",
			"data/eval/phase6_readiness_latest.json",
			"--markdown-out",
			"data/eval/phase6_readiness_packet.md",
		]
		if args.with_observability:
			readiness_cmd.append("--run-observability")
		commands.append(readiness_cmd)

		for command in commands:
			exit_code = _run_command(command)
			if exit_code != 0:
				return exit_code
		return 0

	parser.print_help()
	return 1


if __name__ == "__main__":
	raise SystemExit(main())
