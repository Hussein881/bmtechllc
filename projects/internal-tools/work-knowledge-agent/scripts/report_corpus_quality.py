"""Tool: report_corpus_quality

Tag: reusable-asset

What this tool does:
- Computes Phase 5 corpus quality controls for duplicate content.
- Reports exact-hash dedupe baseline metrics and near-duplicate candidates.
- Emits a JSON report artifact for gate evidence.

Inputs:
- Chunk artifact path.
- Optional near-duplicate threshold and max pair checks.

Outputs:
- Console metrics summary.
- JSON report file containing exact and near-duplicate statistics.

Status:
- Phase 5 corpus quality control baseline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Report corpus duplicate/near-duplicate quality signals.")
	parser.add_argument("--chunks", type=Path, default=Path("data/processed/chunks.jsonl"))
	parser.add_argument("--near-duplicate-threshold", type=float, default=0.93)
	parser.add_argument("--max-pairs-per-source", type=int, default=200)
	parser.add_argument("--report-out", type=Path, default=Path("data/eval/corpus_quality_report_latest.json"))
	return parser.parse_args()


def _load_rows(path: Path) -> list[dict[str, Any]]:
	if not path.exists() or not path.read_text(encoding="utf-8").strip():
		return []
	rows: list[dict[str, Any]] = []
	with path.open("r", encoding="utf-8") as handle:
		for line in handle:
			line = line.strip()
			if not line:
				continue
			try:
				payload = json.loads(line)
			except json.JSONDecodeError:
				continue
			if isinstance(payload, dict):
				rows.append(payload)
	return rows


def _normalize(text: str) -> str:
	return " ".join(str(text or "").lower().split())


def _hash(value: str) -> str:
	return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _near_duplicates_by_source(
	rows: list[dict[str, Any]], threshold: float, max_pairs_per_source: int
) -> tuple[list[dict[str, Any]], int]:
	by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
	for row in rows:
		source = str((row.get("metadata") or {}).get("source_file", "") or "unknown")
		by_source[source].append(row)

	candidates: list[dict[str, Any]] = []
	pairs_checked = 0
	for source, source_rows in by_source.items():
		if len(source_rows) < 2:
			continue
		limit = min(max_pairs_per_source, len(source_rows) * (len(source_rows) - 1) // 2)
		checked_for_source = 0
		for idx, left in enumerate(source_rows):
			left_text = _normalize(str(left.get("content", "")))
			if not left_text:
				continue
			for right in source_rows[idx + 1 :]:
				if checked_for_source >= limit:
					break
				right_text = _normalize(str(right.get("content", "")))
				if not right_text:
					continue
				checked_for_source += 1
				pairs_checked += 1
				ratio = SequenceMatcher(None, left_text, right_text).ratio()
				if ratio < threshold:
					continue
				candidates.append(
					{
						"source_file": source,
						"chunk_id_a": str(left.get("chunk_id", "")),
						"chunk_id_b": str(right.get("chunk_id", "")),
						"similarity": round(float(ratio), 4),
					}
				)
			if checked_for_source >= limit:
				break

	candidates.sort(key=lambda item: float(item.get("similarity", 0.0)), reverse=True)
	return candidates, pairs_checked


def main() -> None:
	args = parse_args()
	rows = _load_rows(args.chunks)
	normalized_rows = []
	hashes: Counter[str] = Counter()
	for row in rows:
		text = _normalize(str(row.get("content", "")))
		if not text:
			continue
		hash_value = _hash(text)
		hashes[hash_value] += 1
		normalized_rows.append(row)

	exact_duplicate_groups = [count for count in hashes.values() if count > 1]
	exact_duplicate_chunk_total = sum(count - 1 for count in exact_duplicate_groups)

	near_candidates, pairs_checked = _near_duplicates_by_source(
		normalized_rows,
		threshold=args.near_duplicate_threshold,
		max_pairs_per_source=args.max_pairs_per_source,
	)

	report = {
		"chunks_path": str(args.chunks),
		"total_chunks": len(normalized_rows),
		"controls": {
			"exact_hash_dedupe": {
				"duplicate_group_count": len(exact_duplicate_groups),
				"duplicate_chunk_total": exact_duplicate_chunk_total,
				"duplicate_rate_pct": round((exact_duplicate_chunk_total / len(normalized_rows) * 100.0) if normalized_rows else 0.0, 3),
			},
			"near_duplicate_strategy": {
				"threshold": args.near_duplicate_threshold,
				"max_pairs_per_source": args.max_pairs_per_source,
				"pairs_checked": pairs_checked,
				"candidate_count": len(near_candidates),
				"top_candidates": near_candidates[:20],
			},
		},
	}

	args.report_out.parent.mkdir(parents=True, exist_ok=True)
	args.report_out.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")

	print("Corpus quality report complete")
	print(f"total_chunks={report['total_chunks']}")
	print(f"exact_duplicate_rate_pct={report['controls']['exact_hash_dedupe']['duplicate_rate_pct']}")
	print(f"near_duplicate_candidate_count={report['controls']['near_duplicate_strategy']['candidate_count']}")
	print(f"report_path={args.report_out}")


if __name__ == "__main__":
	main()
