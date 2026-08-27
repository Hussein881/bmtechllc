"""Tool: run_howto_eval

Tag: reusable-asset

What this tool does:
- Executes a fixed evaluation set against the Phase 3 How-To workflow.
- Reports supported/citation/section/command/source match rates and latency metrics.

Inputs:
- How-To eval cases JSON.
- Retrieval artifact/index paths.
- Optional Watsonx project/url/model overrides.

Outputs:
- Console summary metrics for Gate 3 review.
- JSON report file for trend tracking.

Status:
- Phase 3 How-To evaluation harness.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from work_knowledge_agent.evaluation import verify_golden_dataset
from work_knowledge_agent.evaluation.howto_eval import evaluate_howto_cases, load_howto_eval_cases
from work_knowledge_agent.workflows.howto_workflow import HowToWorkflowConfig


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Run Phase 3 How-To evaluation suite.")
	parser.add_argument("--eval-cases", type=Path, default=Path("data/eval/howto_eval_cases_golden.json"))
	parser.add_argument("--golden-manifest", type=Path, default=Path("data/eval/howto_eval_cases_golden.meta.json"))
	parser.add_argument("--chunks", type=Path, default=Path("data/processed/chunks.jsonl"))
	parser.add_argument("--metadata", type=Path, default=Path("data/processed/metadata.parquet"))
	parser.add_argument("--keyword-index", type=Path, default=Path("data/indexes/keyword/index.json"))
	parser.add_argument("--vector-index", type=Path, default=Path("data/indexes/vector/index.json"))
	parser.add_argument("--top-k", type=int, default=8)
	parser.add_argument("--trials", type=int, default=5, help="Repeated runs to execute per eval case")
	parser.add_argument("--seed", type=int, default=41, help="Fixed seed to use for evaluation requests when supported by the provider")
	parser.add_argument("--min-metadata-confidence", type=float, default=0.30)
	parser.add_argument("--temperature", type=float, default=0.0)
	parser.add_argument("--max-output-tokens", type=int, default=700)
	parser.add_argument("--report-out", type=Path, default=Path("data/eval/howto_report_latest.json"))
	parser.add_argument("--project-id", default="", help="Override DEBUG_AGENT_LLM_WATSONX_PROJECT_ID")
	parser.add_argument("--url", default="", help="Override DEBUG_AGENT_LLM_WATSONX_URL")
	parser.add_argument("--apikey-file", default="", help="Override DEBUG_AGENT_LLM_WATSONX_APIKEY_FILE")
	parser.add_argument("--iam-token-url", default="", help="Override DEBUG_AGENT_LLM_IAM_TOKEN_URL")
	parser.add_argument("--model-id", default="", help="Override WKA_WATSONX_MODEL_ID")
	parser.add_argument("--api-version", default="", help="Override WKA_WATSONX_API_VERSION")
	parser.add_argument("--prompt-version", default="", help="Override WKA_WATSONX_PROMPT_VERSION")
	parser.add_argument("--skip-golden-integrity", action="store_true", help="Skip the golden dataset hash verification step")
	parser.add_argument("--allow-unreviewed-golden", action="store_true", help="Allow execution to continue for diagnostic runs even when the golden set is not yet human-reviewed")
	return parser.parse_args()


def _apply_override(env_key: str, value: str) -> None:
	if value.strip():
		os.environ[env_key] = value.strip()


def main() -> None:
	args = parse_args()
	_apply_override("DEBUG_AGENT_LLM_WATSONX_PROJECT_ID", args.project_id)
	_apply_override("DEBUG_AGENT_LLM_WATSONX_URL", args.url)
	_apply_override("DEBUG_AGENT_LLM_WATSONX_APIKEY_FILE", args.apikey_file)
	_apply_override("DEBUG_AGENT_LLM_IAM_TOKEN_URL", args.iam_token_url)
	_apply_override("WKA_WATSONX_MODEL_ID", args.model_id)
	_apply_override("WKA_WATSONX_API_VERSION", args.api_version)
	_apply_override("WKA_WATSONX_PROMPT_VERSION", args.prompt_version)

	cases = load_howto_eval_cases(args.eval_cases)
	golden_integrity: dict | None = None
	if not args.skip_golden_integrity and "golden" in args.eval_cases.name:
		golden_integrity = verify_golden_dataset(args.eval_cases, args.golden_manifest)
		if not golden_integrity.get("hash_match"):
			raise SystemExit(
				"Golden How-To eval dataset integrity check failed. "
				f"Expected SHA-256 {golden_integrity['expected_sha256']} but found {golden_integrity['actual_sha256']}."
			)
		if not golden_integrity.get("gate_eligible") and not args.allow_unreviewed_golden:
			raise SystemExit(
				"Golden How-To eval dataset is not gate-eligible. "
				f"review_status={golden_integrity['review_status']} reviewer={golden_integrity['reviewer'] or 'unset'} "
				"Use --allow-unreviewed-golden only for diagnostic runs."
			)
	config = HowToWorkflowConfig(
		top_k=args.top_k,
		min_metadata_confidence=args.min_metadata_confidence,
		temperature=args.temperature,
		max_output_tokens=args.max_output_tokens,
		seed=args.seed,
	)
	report = evaluate_howto_cases(
		cases,
		chunks_path=args.chunks,
		metadata_path=args.metadata,
		keyword_index_path=args.keyword_index,
		vector_index_path=args.vector_index,
		config=config,
		trials_per_case=max(1, args.trials),
	)
	if golden_integrity is not None:
		report["golden_integrity"] = golden_integrity

	args.report_out.parent.mkdir(parents=True, exist_ok=True)
	args.report_out.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")

	metrics = report["metrics"]
	print("How-To eval complete")
	print(f"total_cases={report['total_cases']}")
	print(f"trials_per_case={report['trials_per_case']}")
	print(f"total_runs={report['total_runs']}")
	if golden_integrity is not None:
		print(f"golden_hash_match={golden_integrity['hash_match']}")
		print(f"golden_review_status={golden_integrity['review_status']}")
		print(f"golden_gate_eligible={golden_integrity['gate_eligible']}")
	print(f"seed={args.seed}")
	print(f"supported_rate_pct={metrics['supported_rate_pct']}")
	print(f"citation_ok_rate_pct={metrics['citation_ok_rate_pct']}")
	print(f"required_sections_rate_pct={metrics['required_sections_rate_pct']}")
	print(f"expected_command_match_rate_pct={metrics['expected_command_match_rate_pct']}")
	print(f"expected_source_match_rate_pct={metrics['expected_source_match_rate_pct']}")
	print(f"latency_p50_ms={metrics['latency_p50_ms']}")
	print(f"latency_p95_ms={metrics['latency_p95_ms']}")
	print(f"answer_generation_p50_ms={metrics['answer_generation_p50_ms']}")
	print(f"answer_generation_p95_ms={metrics['answer_generation_p95_ms']}")
	print(f"report_path={args.report_out}")


if __name__ == "__main__":
	main()