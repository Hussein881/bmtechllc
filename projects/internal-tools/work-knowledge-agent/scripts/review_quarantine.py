"""Tool: review_quarantine

Tag: reusable-asset

What this tool does:
- Summarizes quarantine backlog by reason/stage/file-type.
- Suggests review cadence and highlights retryable categories.

Inputs:
- Quarantine artifact path (`data/processed/quarantine.jsonl` by default).

Outputs:
- Console or JSON summary with backlog size, breakdown, and retry recommendations.

Status:
- Phase 5 quarantine review baseline.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Summarize quarantine backlog and review recommendations.")
	parser.add_argument("--quarantine", type=Path, default=Path("data/processed/quarantine.jsonl"))
	parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
	return parser.parse_args()


def _load_rows(path: Path) -> list[dict]:
	if not path.exists() or not path.read_text(encoding="utf-8").strip():
		return []
	rows: list[dict] = []
	with path.open("r", encoding="utf-8") as handle:
		for line in handle:
			line = line.strip()
			if not line:
				continue
			try:
				rows.append(json.loads(line))
			except json.JSONDecodeError:
				continue
	return rows


def _source_ext(source_file: str) -> str:
	name = str(source_file or "")
	idx = name.rfind(".")
	if idx < 0:
		return "(none)"
	return name[idx:].lower()


def _cadence_recommendation(backlog_size: int) -> str:
	if backlog_size >= 500:
		return "weekly"
	if backlog_size >= 100:
		return "bi-weekly"
	if backlog_size >= 20:
		return "monthly"
	return "quarterly"


def main() -> None:
	args = parse_args()
	rows = _load_rows(args.quarantine)
	reason_counts: Counter[str] = Counter()
	stage_counts: Counter[str] = Counter()
	ext_counts: Counter[str] = Counter()
	retryable_reasons = {"loader_error", "pdf_empty_extract", "metadata_reject"}

	for row in rows:
		reason_counts[str(row.get("reason", "unknown"))] += 1
		stage_counts[str(row.get("stage", "unknown"))] += 1
		ext_counts[_source_ext(str(row.get("source_file", "")))] += 1

	retryable_total = sum(reason_counts.get(reason, 0) for reason in retryable_reasons)
	summary = {
		"quarantine_path": str(args.quarantine),
		"backlog_size": len(rows),
		"review_cadence_recommendation": _cadence_recommendation(len(rows)),
		"retryable_count": retryable_total,
		"reason_counts": dict(reason_counts),
		"stage_counts": dict(stage_counts),
		"top_file_extensions": dict(ext_counts.most_common(10)),
	}

	if args.json:
		print(json.dumps(summary, ensure_ascii=True, indent=2))
		return

	print("Quarantine review")
	print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
	main()
