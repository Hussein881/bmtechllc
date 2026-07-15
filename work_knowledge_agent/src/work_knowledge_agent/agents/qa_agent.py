"""Citation-first QA agent baseline."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import List

from work_knowledge_agent.retrieval.hybrid_retriever import RetrievalHit


@dataclass(frozen=True)
class QAResponse:
	answer: str
	citations: List[dict]
	supported: bool


def _truncate(text: str, max_chars: int = 280) -> str:
	value = (text or "").strip()
	if len(value) <= max_chars:
		return value
	return value[: max_chars - 3].rstrip() + "..."


def _definition_target(question: str) -> str | None:
	q = (question or "").strip().lower()
	patterns = [
		r"^what\s+is\s+([a-z0-9_./ -]{2,})\??$",
		r"^who\s+is\s+([a-z0-9_./ -]{2,})\??$",
		r"^define\s+([a-z0-9_./ -]{2,})\??$",
	]
	for pattern in patterns:
		m = re.match(pattern, q)
		if not m:
			continue
		target = m.group(1).strip(" ?.")
		tokens = [tok for tok in target.split() if tok not in {"a", "an", "the"}]
		if tokens:
			return tokens[-1]
	return None


def _extract_definition_sentence(term: str, text: str) -> str | None:
	if not term or not text:
		return None
	pattern = re.compile(rf"`?{re.escape(term)}`?\s+is\s+[^\n.]+(?:\.|$)", re.IGNORECASE)
	candidates = [m.group(0).strip() for m in pattern.finditer(text)]
	if not candidates:
		return None

	def score(sentence: str) -> int:
		s = sentence.lower()
		value = 0
		if " is an " in s or " is a " in s:
			value += 3
		if "automation" in s:
			value += 3
		if "tool" in s:
			value += 2
		if "used to" in s:
			value += 2
		if "early development" in s or "warning" in s:
			value -= 4
		if "still" in s:
			value -= 2
		return value

	best = max(candidates, key=score)
	return _truncate(best, max_chars=240)


def build_citation(hit: RetrievalHit) -> dict:
	metadata = hit.metadata or {}
	return {
		"chunk_id": hit.chunk_id,
		"source_file": metadata.get("source_file", "unknown"),
		"section_heading": metadata.get("section_heading", "untitled-section"),
		"confidentiality_level": metadata.get("confidentiality_level", "internal"),
		"score": round(hit.score, 4),
		"provenance": metadata.get("provenance", {}),
	}


def answer_question(question: str, hits: List[RetrievalHit], max_citations: int = 4) -> QAResponse:
	if not hits:
		return QAResponse(
			answer=(
				"Unsupported: I could not find enough grounded evidence to answer this question reliably. "
				"Please refine the query or add more source material."
			),
			citations=[],
			supported=False,
		)

	selected = hits[:max_citations]
	term = _definition_target(question)
	definition_sentence = None
	if term:
		for hit in selected:
			definition_sentence = _extract_definition_sentence(term, hit.content)
			if definition_sentence:
				break

	lines = [f"Question: {question.strip()}", ""]
	if definition_sentence:
		lines.extend(["Direct answer:", definition_sentence, ""])

	lines.append("Evidence-based answer:")
	for idx, hit in enumerate(selected, start=1):
		snippet = _truncate(hit.content)
		lines.append(f"{idx}. {snippet}")

	citations = [build_citation(hit) for hit in selected]
	return QAResponse(answer="\n".join(lines), citations=citations, supported=True)
