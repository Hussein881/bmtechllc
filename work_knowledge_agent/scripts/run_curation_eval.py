"""Tool: run_curation_eval

Tag: reusable-asset

What this tool does:
- Executes a fixed evaluation set against the Phase 5 curation workflow.
- Reports expected proposal-type match, proposal presence, and latency metrics.

Inputs:
- Curation eval cases JSON.
- Retrieval artifact/index paths.

Outputs:
- Console summary metrics for Phase 5 review.
- JSON report file for trend tracking.

Status:
- Phase 5 curation evaluation harness.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from work_knowledge_agent.evaluation.curation_eval import evaluate_curation_cases, load_curation_eval_cases
from work_knowledge_agent.workflows.curation_workflow import CurationWorkflowConfig


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Run Phase 5 curation evaluation suite.")
	parser.add_argument("--eval-cases", type=Path, default=Path("data/eval/curation_eval_cases.json"))
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
	parser.add_argument("--report-out", type=Path, default=Path("data/eval/curation_report_latest.json"))
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	cases = load_curation_eval_cases(args.eval_cases)
	config = CurationWorkflowConfig(
		top_k=args.top_k,
		min_metadata_confidence=args.min_metadata_confidence,
		duplicate_similarity_threshold=args.duplicate_similarity_threshold,
		outdated_year_cutoff=args.outdated_year_cutoff,
		allowed_confidentiality=tuple(args.allowed_confidentiality),
		min_query_token_coverage=args.min_query_token_coverage,
	)
	report = evaluate_curation_cases(
		cases,
		chunks_path=args.chunks,
		metadata_path=args.metadata,
		keyword_index_path=args.keyword_index,
		vector_index_path=args.vector_index,
		config=config,
	)

	args.report_out.parent.mkdir(parents=True, exist_ok=True)
	args.report_out.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")

	metrics = report["metrics"]
	print("Curation eval complete")
	print(f"total_cases={report['total_cases']}")
	print(f"total_runs={report['total_runs']}")
	print(f"expected_type_match_rate_pct={metrics['expected_type_match_rate_pct']}")
	print(f"non_empty_proposal_rate_pct={metrics['non_empty_proposal_rate_pct']}")
	print(f"proposal_count_avg={metrics['proposal_count_avg']}")
	print(f"latency_p50_ms={metrics['latency_p50_ms']}")
	print(f"latency_p95_ms={metrics['latency_p95_ms']}")
	print(f"report_path={args.report_out}")


if __name__ == "__main__":
	main()
