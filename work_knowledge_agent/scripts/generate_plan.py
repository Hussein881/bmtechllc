"""Tool: generate_plan

Tag: reusable-asset

What this tool will do (planned):
- Turn vague engineering goals into actionable task checklists.
- Highlight dependencies and missing context questions.

Status:
- Phase 4 baseline implementation.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from work_knowledge_agent.workflows.planning_workflow import PlanningWorkflowConfig, run_planning_workflow


def _format_duration_ms(milliseconds: float) -> str:
	if milliseconds < 1000.0:
		return f"{milliseconds:.3f}ms"
	seconds = milliseconds / 1000.0
	if seconds < 60.0:
		return f"{seconds:.3f}s"
	minutes = seconds / 60.0
	if minutes < 60.0:
		return f"{minutes:.3f}min"
	hours = minutes / 60.0
	return f"{hours:.3f}hr"


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Generate a structured plan from indexed artifacts.")
	parser.add_argument("goal", help="Goal or planning request")
	parser.add_argument("--chunks", type=Path, default=Path("data/processed/chunks.jsonl"))
	parser.add_argument("--metadata", type=Path, default=Path("data/processed/metadata.parquet"))
	parser.add_argument("--keyword-index", type=Path, default=Path("data/indexes/keyword/index.json"))
	parser.add_argument("--vector-index", type=Path, default=Path("data/indexes/vector/index.json"))
	parser.add_argument("--top-k", type=int, default=8)
	parser.add_argument("--min-metadata-confidence", type=float, default=0.30)
	parser.add_argument(
		"--allowed-confidentiality",
		nargs="+",
		default=["public", "internal", "confidential"],
		help="Allowed confidentiality levels",
	)
	parser.add_argument("--temperature", type=float, default=0.0)
	parser.add_argument("--max-output-tokens", type=int, default=700)
	parser.add_argument("--project-id", default="", help="Override DEBUG_AGENT_LLM_WATSONX_PROJECT_ID")
	parser.add_argument("--url", default="", help="Override DEBUG_AGENT_LLM_WATSONX_URL")
	parser.add_argument("--apikey-file", default="", help="Override DEBUG_AGENT_LLM_WATSONX_APIKEY_FILE")
	parser.add_argument("--iam-token-url", default="", help="Override DEBUG_AGENT_LLM_IAM_TOKEN_URL")
	parser.add_argument("--model-id", default="", help="Override WKA_WATSONX_MODEL_ID")
	parser.add_argument("--api-version", default="", help="Override WKA_WATSONX_API_VERSION")
	parser.add_argument("--prompt-version", default="", help="Override WKA_WATSONX_PROMPT_VERSION")
	parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
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
	config = PlanningWorkflowConfig(
		top_k=args.top_k,
		min_metadata_confidence=args.min_metadata_confidence,
		allowed_confidentiality=tuple(args.allowed_confidentiality),
		temperature=args.temperature,
		max_output_tokens=args.max_output_tokens,
	)
	result = run_planning_workflow(
		goal=args.goal,
		chunks_path=args.chunks,
		metadata_path=args.metadata,
		keyword_index_path=args.keyword_index,
		vector_index_path=args.vector_index,
		config=config,
	)

	if args.json:
		payload = {
			"answer": result.response.answer,
			"supported": result.response.supported,
			"citations": result.response.citations,
			"guardrail_status": result.guardrail_status,
			"stage_times_ms": result.stage_times_ms,
			"generation_metadata": result.generation_metadata,
			"retrieval_hit_count": len(result.retrieval_hits),
		}
		print(json.dumps(payload, ensure_ascii=True, indent=2))
		return

	print("Plan Result")
	print(result.response.answer)
	print("")
	print(f"supported={result.response.supported}")
	print(f"retrieval_hits={len(result.retrieval_hits)}")
	print(f"boundary_allowed={result.guardrail_status.get('boundary_allowed')}")
	print(f"guardrail_citation_ok={result.guardrail_status.get('citation_ok')}")
	for stage, ms in result.stage_times_ms.items():
		print(f"stage_{stage}={_format_duration_ms(ms)}")
		print(f"stage_{stage}_ms={ms}")
	print("generation_metadata=")
	print(json.dumps(result.generation_metadata, ensure_ascii=True, indent=2))
	print("citations=")
	for citation in result.response.citations:
		print(json.dumps(citation, ensure_ascii=True))


if __name__ == "__main__":
	main()

