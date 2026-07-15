"""Tool: triage_curation

Tag: reusable-asset

What this tool does:
- Runs Phase 5 curation proposal generation for a topic.
- Applies reviewer triage dispositions (accepted/deferred/rejected).
- Enforces a human-approval checkpoint for accepted proposals.
- Persists a triage record JSON for audit and follow-up.

Inputs:
- Topic prompt.
- Optional decisions JSON file.
- Retrieval/index artifacts and workflow controls.

Outputs:
- Console or JSON triage output.
- Optional persisted triage record file.

Status:
- Phase 5 triage + approval baseline.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import sys
from pathlib import Path
from typing import Any

from work_knowledge_agent.workflows.curation_triage_workflow import run_curation_triage_workflow
from work_knowledge_agent.workflows.curation_workflow import CurationWorkflowConfig, run_curation_workflow


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Apply triage decisions to curator proposals with human-approval checks.")
	parser.add_argument("topic", help="Topic or area to assess for curation")
	parser.add_argument("--decisions", type=Path, default=None, help="Path to triage decisions JSON")
	parser.add_argument("--output", type=Path, default=Path("data/eval/curation_triage_latest.json"), help="Output JSON report path")
	parser.add_argument("--history", type=Path, default=Path("data/eval/curation_triage_history.jsonl"), help="Append-only triage history JSONL path")
	parser.add_argument("--default-disposition", choices=["accepted", "deferred", "rejected"], default="deferred")
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
	parser.add_argument("--proposal-generated-at", default="", help="Optional ISO timestamp for proposal creation time")
	parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
	return parser.parse_args()


def _load_decisions(path: Path | None) -> tuple[list[dict[str, Any]], str | None, str | None]:
	if path is None:
		return [], None, None
	if not path.exists() or not path.read_text(encoding="utf-8").strip():
		return [], None, None
	payload = json.loads(path.read_text(encoding="utf-8"))
	if isinstance(payload, list):
		return [row for row in payload if isinstance(row, dict)], None, None
	if not isinstance(payload, dict):
		return [], None, None
	rows = payload.get("decisions", [])
	if not isinstance(rows, list):
		rows = []
	default_disposition = payload.get("default_disposition")
	if default_disposition is not None:
		default_disposition = str(default_disposition).strip().lower()
	proposal_generated_at = payload.get("proposal_generated_at_utc")
	if proposal_generated_at is not None:
		proposal_generated_at = str(proposal_generated_at).strip()
	return [row for row in rows if isinstance(row, dict)], default_disposition, proposal_generated_at


def _write_output(path: Path, payload: dict[str, Any]) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def _append_history_snapshot(path: Path, payload: dict[str, Any], channel: str, output_path: Path) -> None:
	event = {
		"event_type": "triage_snapshot",
		"event_timestamp_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
		"channel": channel,
		"output_path": str(output_path),
		"topic": ((payload.get("summary") or {}).get("topic", "") if isinstance(payload, dict) else ""),
		"triage_summary": ((payload.get("triage") or {}).get("summary", {}) if isinstance(payload, dict) else {}),
		"payload": payload,
	}
	path.parent.mkdir(parents=True, exist_ok=True)
	with path.open("a", encoding="utf-8") as handle:
		handle.write(json.dumps(event, ensure_ascii=True) + "\n")


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
	curation_result = run_curation_workflow(
		topic=args.topic,
		chunks_path=args.chunks,
		metadata_path=args.metadata,
		keyword_index_path=args.keyword_index,
		vector_index_path=args.vector_index,
		config=config,
	)
	decision_rows, file_default, file_generated_at = _load_decisions(args.decisions)
	default_disposition = file_default or args.default_disposition
	proposal_generated_at_utc = file_generated_at or str(args.proposal_generated_at or "").strip() or None
	try:
		triage_result = run_curation_triage_workflow(
			topic=args.topic,
			proposals=curation_result.proposals,
			decision_rows=decision_rows,
			default_disposition=default_disposition,
			proposal_generated_at_utc=proposal_generated_at_utc,
			decision_channel="cli",
		)
	except (PermissionError, ValueError) as exc:
		print(f"triage_error={exc}", file=sys.stderr)
		raise SystemExit(2)

	payload = {
		"summary": {
			"topic": args.topic,
			"curation": curation_result.summary,
			"triage": triage_result.summary,
		},
		"stage_times_ms": curation_result.stage_times_ms,
		"retrieval_hit_count": len(curation_result.retrieval_hits),
		"triage": triage_result.to_dict(),
	}
	_write_output(args.output, payload)
	_append_history_snapshot(args.history, payload, channel="cli", output_path=args.output)

	if args.json:
		print(json.dumps(payload, ensure_ascii=True, indent=2))
		return

	print("Curation triage result")
	print(json.dumps(payload["summary"], ensure_ascii=True, indent=2))
	print(f"saved_output={args.output}")


if __name__ == "__main__":
	main()
