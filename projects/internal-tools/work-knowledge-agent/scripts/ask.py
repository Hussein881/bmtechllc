"""Tool: ask

Tag: reusable-asset

What this tool does:
- Accepts a user question.
- Runs hybrid retrieval over processed chunk and index artifacts.
- Applies confidentiality, unsupported-step, and citation guardrails.
- Produces a citation-first answer with provenance-backed sources.

Inputs:
- Question string.
- Paths to chunks, metadata, keyword index, and vector index artifacts.
- Retrieval controls (`top_k`, confidence threshold, allowed confidentiality levels).

Outputs:
- Human-readable Q&A response with guardrail status and citations.
- Optional JSON payload containing answer, citations, support status, and hit count.

Status:
- Phase 2 baseline implementation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from work_knowledge_agent.workflows.qa_workflow import QAWorkflowConfig, run_qa_workflow


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
	parser = argparse.ArgumentParser(description="Ask a citation-first question against indexed artifacts.")
	parser.add_argument("question", help="Question to ask")
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
	parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	config = QAWorkflowConfig(
		top_k=args.top_k,
		min_metadata_confidence=args.min_metadata_confidence,
		allowed_confidentiality=tuple(args.allowed_confidentiality),
	)
	result = run_qa_workflow(
		question=args.question,
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
			"retrieval_hit_count": len(result.retrieval_hits),
		}
		print(json.dumps(payload, ensure_ascii=True, indent=2))
		return

	print("Q&A Result")
	print(result.response.answer)
	print("")
	print(f"supported={result.response.supported}")
	print(f"retrieval_hits={len(result.retrieval_hits)}")
	print(f"guardrail_supported={result.guardrail_status.get('supported')}")
	print(f"guardrail_citation_ok={result.guardrail_status.get('citation_ok')}")
	for stage, ms in result.stage_times_ms.items():
		print(f"stage_{stage}={_format_duration_ms(ms)}")
		print(f"stage_{stage}_ms={ms}")
	print("citations=")
	for citation in result.response.citations:
		print(json.dumps(citation, ensure_ascii=True))


if __name__ == "__main__":
	main()

