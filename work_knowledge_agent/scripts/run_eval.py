"""Tool: run_eval

Tag: reusable-asset

What this tool does:
- Executes a fixed evaluation set against the Phase 2 Q&A workflow.
- Reports retrieval/citation/refusal/performance metrics.

Inputs:
- Eval question set JSON.
- Expected source mappings JSON.
- Artifact/index paths used by retrieval.

Outputs:
- Console summary metrics for gate review.
- JSON report file for trend tracking.

Status:
- Phase 2 baseline implementation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import median

from work_knowledge_agent.workflows.qa_workflow import QAWorkflowConfig, run_qa_workflow


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Run Phase 2 evaluation suite.")
	parser.add_argument("--eval-questions", type=Path, default=Path("data/eval/eval_questions.json"))
	parser.add_argument("--expected-sources", type=Path, default=Path("data/eval/expected_sources.json"))
	parser.add_argument("--chunks", type=Path, default=Path("data/processed/chunks.jsonl"))
	parser.add_argument("--metadata", type=Path, default=Path("data/processed/metadata.parquet"))
	parser.add_argument("--keyword-index", type=Path, default=Path("data/indexes/keyword/index.json"))
	parser.add_argument("--vector-index", type=Path, default=Path("data/indexes/vector/index.json"))
	parser.add_argument("--top-k", type=int, default=8)
	parser.add_argument("--min-metadata-confidence", type=float, default=0.30)
	parser.add_argument("--report-out", type=Path, default=Path("data/eval/report_latest.json"))
	return parser.parse_args()


def _load_json(path: Path, default):
	if not path.exists() or not path.read_text(encoding="utf-8").strip():
		return default
	return json.loads(path.read_text(encoding="utf-8"))


def _percent(num: int, den: int) -> float:
	return (num / den * 100.0) if den else 0.0


def _p95(values: list[float]) -> float:
	if not values:
		return 0.0
	sorted_vals = sorted(values)
	idx = min(len(sorted_vals) - 1, int(round(0.95 * (len(sorted_vals) - 1))))
	return float(sorted_vals[idx])


def _source_match(paths: list[str], expected_substrings: list[str]) -> bool:
	if not expected_substrings:
		return True
	for expected in expected_substrings:
		if any(expected in value for value in paths):
			return True
	return False


def main() -> None:
	args = parse_args()
	eval_questions = _load_json(args.eval_questions, [])
	expected_sources = _load_json(args.expected_sources, {})

	config = QAWorkflowConfig(
		top_k=args.top_k,
		min_metadata_confidence=args.min_metadata_confidence,
	)

	total = 0
	answerable_total = 0
	unanswerable_total = 0
	refusal_correct = 0
	citation_pass = 0
	retrieval_source_hit = 0
	citation_source_hit = 0
	latencies: list[float] = []

	per_question: list[dict] = []
	for row in eval_questions:
		question_id = str(row.get("id", "")).strip() or f"q-{total+1}"
		question = str(row.get("question", "")).strip()
		if not question:
			continue
		expected_answerable = bool(row.get("expected_answerable", True))
		expected = list(expected_sources.get(question_id, row.get("expected_sources", [])))

		result = run_qa_workflow(
			question=question,
			chunks_path=args.chunks,
			metadata_path=args.metadata,
			keyword_index_path=args.keyword_index,
			vector_index_path=args.vector_index,
			config=config,
		)

		total += 1
		if expected_answerable:
			answerable_total += 1
		else:
			unanswerable_total += 1
			if not result.response.supported:
				refusal_correct += 1

		if result.guardrail_status.get("citation_ok"):
			citation_pass += 1

		retrieved_sources = [str(hit.metadata.get("source_file", "")) for hit in result.retrieval_hits]
		citation_sources = [str(cit.get("source_file", "")) for cit in result.response.citations]
		if _source_match(retrieved_sources, expected):
			retrieval_source_hit += 1
		if _source_match(citation_sources, expected):
			citation_source_hit += 1

		latencies.append(float(result.stage_times_ms.get("total", 0.0)))
		per_question.append(
			{
				"id": question_id,
				"question": question,
				"expected_answerable": expected_answerable,
				"supported": result.response.supported,
				"citation_ok": result.guardrail_status.get("citation_ok"),
				"retrieval_hits": len(result.retrieval_hits),
				"expected_sources": expected,
				"retrieved_sources": retrieved_sources,
				"citation_sources": citation_sources,
				"stage_times_ms": result.stage_times_ms,
			}
		)

	report = {
		"total_questions": total,
		"metrics": {
			"citation_guardrail_pass_rate_pct": round(_percent(citation_pass, total), 3),
			"retrieval_source_hit_rate_pct": round(_percent(retrieval_source_hit, total), 3),
			"citation_source_hit_rate_pct": round(_percent(citation_source_hit, total), 3),
			"refusal_accuracy_pct": round(_percent(refusal_correct, unanswerable_total), 3),
			"latency_p50_ms": round(float(median(latencies)) if latencies else 0.0, 3),
			"latency_p95_ms": round(_p95(latencies), 3),
		},
		"per_question": per_question,
	}

	args.report_out.parent.mkdir(parents=True, exist_ok=True)
	args.report_out.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")

	print("Eval complete")
	print(f"total_questions={total}")
	print(f"citation_guardrail_pass_rate_pct={report['metrics']['citation_guardrail_pass_rate_pct']}")
	print(f"retrieval_source_hit_rate_pct={report['metrics']['retrieval_source_hit_rate_pct']}")
	print(f"citation_source_hit_rate_pct={report['metrics']['citation_source_hit_rate_pct']}")
	print(f"refusal_accuracy_pct={report['metrics']['refusal_accuracy_pct']}")
	print(f"latency_p50_ms={report['metrics']['latency_p50_ms']}")
	print(f"latency_p95_ms={report['metrics']['latency_p95_ms']}")
	print(f"report_path={args.report_out}")


if __name__ == "__main__":
	main()

