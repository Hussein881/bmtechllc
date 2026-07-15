"""Tool: build_indexes

Tag: reusable-asset

What this tool does:
- Reads chunk artifacts produced by ingestion.
- Builds a keyword postings index for lexical retrieval.
- Builds a lightweight TF-IDF-style vector index for semantic-like scoring.

Inputs:
- Chunk JSONL artifact path.
- Output directories for keyword and vector indexes.

Outputs:
- `data/indexes/keyword/index.json` (or user-provided path)
- `data/indexes/vector/index.json` (or user-provided path)
- Console summary with chunk count and output paths.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List

TOKEN_RE = re.compile(r"[A-Za-z0-9_]{2,}")


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
	parser = argparse.ArgumentParser(description="Build retrieval indexes from chunk artifacts.")
	parser.add_argument("--chunks", type=Path, default=Path("data/processed/chunks.jsonl"))
	parser.add_argument("--keyword-dir", type=Path, default=Path("data/indexes/keyword"))
	parser.add_argument("--vector-dir", type=Path, default=Path("data/indexes/vector"))
	return parser.parse_args()


def _load_chunks(path: Path) -> List[dict]:
	chunks: List[dict] = []
	if not path.exists():
		return chunks
	with path.open("r", encoding="utf-8") as handle:
		for line in handle:
			line = line.strip()
			if not line:
				continue
			chunks.append(json.loads(line))
	return chunks


def _tokenize(text: str) -> List[str]:
	return [token.lower() for token in TOKEN_RE.findall(text or "")]


def build_keyword_index(chunks: Iterable[dict]) -> dict:
	postings: Dict[str, List[str]] = defaultdict(list)
	inverted_index: Dict[str, Dict[str, int]] = defaultdict(dict)
	doc_lengths: Dict[str, int] = {}
	total_length = 0
	docs = list(chunks)
	for chunk in docs:
		chunk_id = str(chunk.get("chunk_id", "")).strip()
		if not chunk_id:
			continue
		tokens = _tokenize(chunk.get("content", ""))
		doc_len = len(tokens)
		doc_lengths[chunk_id] = doc_len
		total_length += doc_len
		counts = Counter(tokens)
		for token, tf in counts.items():
			inverted_index[token][chunk_id] = int(tf)
			postings[token].append(chunk_id)

	total_docs = max(1, len(doc_lengths))
	avgdl = (total_length / total_docs) if total_docs else 0.0
	doc_freq = {token: len(doc_map) for token, doc_map in inverted_index.items()}
	return {
		"model": "bm25-lite",
		"k1": 1.2,
		"b": 0.75,
		"total_docs": total_docs,
		"avgdl": round(avgdl, 6),
		"doc_lengths": doc_lengths,
		"doc_freq": doc_freq,
		"inverted_index": inverted_index,
		"postings": dict(postings),
	}


def build_vector_index(chunks: Iterable[dict]) -> dict:
	docs = list(chunks)
	doc_tokens = [Counter(_tokenize(chunk.get("content", ""))) for chunk in docs]
	df = Counter()
	for counts in doc_tokens:
		for token in counts:
			df[token] += 1

	total_docs = max(1, len(docs))
	vectors = {}
	for chunk, counts in zip(docs, doc_tokens):
		chunk_id = chunk.get("chunk_id")
		weights = {}
		for token, tf in counts.items():
			idf = math.log((1 + total_docs) / (1 + df[token])) + 1.0
			weights[token] = round(float(tf) * idf, 6)
		vectors[chunk_id] = {
			"weights": dict(sorted(weights.items(), key=lambda item: item[1], reverse=True)[:128])
		}

	return {"model": "tfidf-lite", "vectors": vectors}


def _write_json(path: Path, payload: dict) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def main() -> None:
	args = parse_args()
	start_total = time.perf_counter()
	start_load = time.perf_counter()
	chunks = _load_chunks(args.chunks)
	load_ms = (time.perf_counter() - start_load) * 1000.0

	start_keyword = time.perf_counter()
	keyword_index = build_keyword_index(chunks)
	keyword_ms = (time.perf_counter() - start_keyword) * 1000.0
	start_vector = time.perf_counter()
	vector_index = build_vector_index(chunks)
	vector_ms = (time.perf_counter() - start_vector) * 1000.0

	keyword_path = args.keyword_dir / "index.json"
	vector_path = args.vector_dir / "index.json"

	start_write = time.perf_counter()
	_write_json(keyword_path, keyword_index)
	_write_json(vector_path, vector_index)
	write_ms = (time.perf_counter() - start_write) * 1000.0
	total_ms = (time.perf_counter() - start_total) * 1000.0

	print("Index build complete")
	print(f"chunks={len(chunks)}")
	print(f"keyword_index={keyword_path}")
	print(f"vector_index={vector_path}")
	print(f"stage_load={_format_duration_ms(load_ms)}")
	print(f"stage_load_ms={round(load_ms, 3)}")
	print(f"stage_keyword={_format_duration_ms(keyword_ms)}")
	print(f"stage_keyword_ms={round(keyword_ms, 3)}")
	print(f"stage_vector={_format_duration_ms(vector_ms)}")
	print(f"stage_vector_ms={round(vector_ms, 3)}")
	print(f"stage_write={_format_duration_ms(write_ms)}")
	print(f"stage_write_ms={round(write_ms, 3)}")
	print(f"stage_total={_format_duration_ms(total_ms)}")
	print(f"stage_total_ms={round(total_ms, 3)}")


if __name__ == "__main__":
	main()

