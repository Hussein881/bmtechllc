"""Tool: generate_curation

Tag: reusable-asset

What this tool does:
- Runs the Phase 5 curation workflow for a topic.
- Returns proposal suggestions for missing, duplicate, or outdated knowledge.

Inputs:
- Topic prompt describing what area to curate.
- Retrieval/index artifact paths and filtering options.

Outputs:
- Console or JSON output containing curation proposals and diagnostics.

Status:
- Phase 5 baseline implementation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from work_knowledge_agent.workflows.curation_workflow import CurationWorkflowConfig, run_curation_workflow


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Generate curation proposals from indexed artifacts.")
	parser.add_argument("topic", help="Topic or area to assess for curation")
	parser.add_argument("--chunks", type=Path, default=Path("data/processed/chunks.jsonl"))
	parser.add_argument("--metadata", type=Path, default=Path("data/processed/metadata.parquet"))
	parser.add_argument("--keyword-index", type=Path, default=Path("data/indexes/keyword/index.json"))
	parser.add_argument("--vector-index", type=Path, default=Path("data/indexes/vector/index.json"))
	parser.add_argument("--top-k", type=int, default=12)
	parser.add_argument("--min-metadata-confidence", type=float, default=0.30)
	parser.add_argument("--duplicate-similarity-threshold", type=float, default=0.92)
	parser.add_argument("--outdated-year-cutoff", type=int, default=2021)
	parser.add_argument(
		"--allowed-confidentiality",
		nargs="+",
		default=["public", "internal", "confidential"],
		help="Allowed confidentiality levels",
	)
	parser.add_argument("--min-query-token-coverage", type=float, default=0.40)
	parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	config = CurationWorkflowConfig(
		top_k=args.top_k,
		min_metadata_confidence=args.min_metadata_confidence,
		duplicate_similarity_threshold=args.duplicate_similarity_threshold,
		outdated_year_cutoff=args.outdated_year_cutoff,
		allowed_confidentiality=tuple(args.allowed_confidentiality),
		min_query_token_coverage=args.min_query_token_coverage,
	)
	result = run_curation_workflow(
		topic=args.topic,
		chunks_path=args.chunks,
		metadata_path=args.metadata,
		keyword_index_path=args.keyword_index,
		vector_index_path=args.vector_index,
		config=config,
	)

	payload = {
		"summary": result.summary,
		"stage_times_ms": result.stage_times_ms,
		"retrieval_hit_count": len(result.retrieval_hits),
		"proposals": [proposal.to_dict() for proposal in result.proposals],
	}

	if args.json:
		print(json.dumps(payload, ensure_ascii=True, indent=2))
		return

	print("Curation Result")
	print(json.dumps(result.summary, ensure_ascii=True, indent=2))
	print("proposals=")
	for proposal in result.proposals:
		print(json.dumps(proposal.to_dict(), ensure_ascii=True))


if __name__ == "__main__":
	main()
