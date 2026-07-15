"""Citation guardrail checks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List

TOKEN_RE = re.compile(r"[A-Za-z0-9_]{3,}")
COMMAND_RE = re.compile(r"(?m)^\s*(?:[-*]\s*)?(\$\s*[^\n]+|sudo\s+\S[^\n]*|kubectl\s+[^\n]+|docker\s+[^\n]+)")


@dataclass(frozen=True)
class CitationCheckResult:
	passed: bool
	reason: str
	details: dict


def _tokens(text: str) -> set[str]:
	return {token.lower() for token in TOKEN_RE.findall(text or "")}


def _grounding_ratio(answer_text: str, evidence_text: str) -> float:
	answer_tokens = _tokens(answer_text)
	evidence_tokens = _tokens(evidence_text)
	if not answer_tokens or not evidence_tokens:
		return 0.0
	overlap = answer_tokens & evidence_tokens
	return len(overlap) / max(1, len(answer_tokens))


def _extract_commands(text: str) -> List[str]:
	commands: List[str] = []
	for match in COMMAND_RE.finditer(text or ""):
		command = (match.group(1) or "").strip()
		if command and not re.match(r"^sudo\s+(?:or|and|privileges?)\b", command, re.IGNORECASE):
			commands.append(command)
	return commands


def _command_variants(command: str) -> List[str]:
	value = (command or "").strip()
	if not value:
		return []

	variants = [value]
	normalized = value.lstrip("$ ").strip()
	if normalized and normalized not in variants:
		variants.append(normalized)

	if normalized.lower().startswith("sudo "):
		without_sudo = normalized[5:].strip()
		if without_sudo and without_sudo not in variants:
			variants.append(without_sudo)
		if without_sudo.startswith("./"):
			without_dot = without_sudo[2:].strip()
			if without_dot and without_dot not in variants:
				variants.append(without_dot)

	if normalized.startswith("./"):
		without_dot = normalized[2:].strip()
		if without_dot and without_dot not in variants:
			variants.append(without_dot)

	return variants


def enforce_citation_guardrail(
	answer_text: str,
	citations: List[dict],
	evidence_by_chunk: Dict[str, str] | None = None,
	grounding_threshold: float = 0.12,
) -> CitationCheckResult:
	if not answer_text.strip():
		return CitationCheckResult(passed=False, reason="empty_answer", details={})
	if not citations:
		return CitationCheckResult(passed=False, reason="missing_citations", details={})

	valid = [c for c in citations if str(c.get("source_file", "")).strip()]
	if not valid:
		return CitationCheckResult(passed=False, reason="invalid_citations", details={})

	evidence_map = evidence_by_chunk or {}
	if evidence_map:
		evidence_text = "\n\n".join(evidence_map.values())
		grounding = _grounding_ratio(answer_text, evidence_text)
		if grounding < grounding_threshold:
			return CitationCheckResult(
				passed=False,
				reason="grounding_below_threshold",
				details={"grounding_ratio": round(grounding, 4)},
			)

		answer_commands = _extract_commands(answer_text)
		if answer_commands:
			evidence_joined = "\n".join(evidence_map.values())
			for command in answer_commands:
				if "..." in command:
					continue
				variants = _command_variants(command)
				if not any(variant and variant in evidence_joined for variant in variants):
					return CitationCheckResult(
						passed=False,
						reason="command_not_in_evidence",
						details={"command": command},
					)

	return CitationCheckResult(passed=True, reason="ok", details={})
