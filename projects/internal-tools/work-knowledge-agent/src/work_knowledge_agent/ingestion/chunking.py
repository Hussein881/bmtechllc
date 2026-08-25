"""Chunking utilities for ingestion."""

from __future__ import annotations

import re
from typing import List

CHUNKER_VERSION = "2.0.0"
HEADING_RE = re.compile(r"(?m)^\s{0,3}#{1,6}\s+.+$")


def _split_by_headings(text: str) -> List[str]:
	parts: List[str] = []
	indices = [match.start() for match in HEADING_RE.finditer(text)]
	if not indices:
		return [text]
	indices.append(len(text))
	for i in range(len(indices) - 1):
		piece = text[indices[i] : indices[i + 1]].strip()
		if piece:
			parts.append(piece)
	return parts


def _safe_split_large_paragraph(paragraph: str, chunk_size: int, overlap: int) -> List[str]:
	"""Split large sections while preserving fenced code-block integrity."""
	if "```" in paragraph:
		# Keep fenced blocks intact even if larger than chunk_size.
		return [paragraph.strip()]

	parts: List[str] = []
	start = 0
	step = chunk_size - overlap
	while start < len(paragraph):
		part = paragraph[start : start + chunk_size].strip()
		if part:
			parts.append(part)
		start += step
	return parts


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 150) -> List[str]:
	"""Split text into overlapping chunks.

	Strategy:
	- split by headings first when available,
	- accumulate paragraph-aware chunks per section,
	- preserve fenced code blocks as atomic units,
	- fall back to fixed windows only for non-code oversized paragraphs.
	"""
	clean = (text or "").strip()
	if not clean:
		return []

	if chunk_size <= 0:
		raise ValueError("chunk_size must be > 0")
	if overlap < 0:
		raise ValueError("overlap must be >= 0")
	if overlap >= chunk_size:
		raise ValueError("overlap must be smaller than chunk_size")

	sections = _split_by_headings(clean)
	chunks: List[str] = []

	for section in sections:
		paragraphs = [p.strip() for p in section.split("\n\n") if p.strip()]
		current = ""
		for para in paragraphs:
			candidate = para if not current else f"{current}\n\n{para}"
			if len(candidate) <= chunk_size:
				current = candidate
				continue

			if current:
				chunks.append(current.strip())
				tail = current[-overlap:] if overlap else ""
				current = f"{tail}\n\n{para}".strip()
			else:
				chunks.extend(_safe_split_large_paragraph(para, chunk_size, overlap))
				current = ""

		if current.strip():
			chunks.append(current.strip())

	return chunks

