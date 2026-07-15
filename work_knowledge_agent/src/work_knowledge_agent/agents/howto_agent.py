"""Structured How-To agent helpers for Phase 3."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from work_knowledge_agent.agents.qa_agent import build_citation
from work_knowledge_agent.retrieval.hybrid_retriever import RetrievalHit

REQUIRED_SECTIONS: tuple[str, ...] = (
	"Summary",
	"Assumptions",
	"Prerequisites",
	"Steps",
	"Commands",
	"Validation",
	"Failure Modes",
	"Sources",
)

SECTION_RE = re.compile(r"(?ms)^##\s+(?P<section>[A-Za-z ]+)\n(?P<body>.*?)(?=^##\s+[A-Za-z ]+\n|\Z)")
EVIDENCE_COMMAND_RE = re.compile(r"(?m)^\s*(\$\s*[^\n]+|\.\/[^\n]+|sudo\s+[^\n]+|systemctl\s+[^\n]+|journalctl\s+[^\n]+|df\s+[^\n]+|du\s+[^\n]+|find\s+[^\n]+)")
BACKTICK_COMMAND_RE = re.compile(r"`(?P<cmd>(?:sudo\s+)?(?:\./)?(?:systemctl|journalctl|df|du|find|ls|cd|pwd|mkdir|rm|grep|awk|sed|cat|tail|head|ps|top|free|uname|ifconfig|ip)\b[^`]*)`")
INLINE_COMMAND_RE = re.compile(r"(?P<cmd>(?:journalctl\b[^\n;|)]*|find\s+/[^\n;|)]*|du\s+-[^\n;|)]*|df\s+-[^\n;|)]*))")


@dataclass(frozen=True)
class HowToResponse:
	answer: str
	citations: List[dict]
	supported: bool


def build_howto_prompt(task: str) -> str:
	return (
		"You are generating a grounded engineering how-to from retrieved evidence only.\n"
		"Use only the supplied retrieved context. Do not invent commands, file paths, steps, or assumptions.\n"
		"Be concise. Prefer short bullet points and minimal explanation.\n"
		"Do not restate the same evidence in multiple sections.\n"
		"In the Commands section, list only executable commands or script invocations.\n"
		"If evidence is weak or missing, state that explicitly inside the relevant section.\n"
		"Return markdown using these exact section headers in this exact order:\n"
		"## Summary\n"
		"## Assumptions\n"
		"## Prerequisites\n"
		"## Steps\n"
		"## Commands\n"
		"## Validation\n"
		"## Failure Modes\n"
		"## Sources\n\n"
		f"Task: {task.strip()}"
	)


def build_evidence_context(hits: List[RetrievalHit], max_evidence_chars: int = 3200) -> str:
	blocks: list[str] = []
	remaining = max_evidence_chars
	for idx, hit in enumerate(hits, start=1):
		metadata = hit.metadata or {}
		content = (hit.content or "").strip()
		if not content:
			continue
		block = (
			f"[Evidence {idx}]\n"
			f"Source File: {metadata.get('source_file', 'unknown')}\n"
			f"Section: {metadata.get('section_heading', 'untitled-section')}\n"
			f"Content:\n{content}\n"
		)
		if len(block) > remaining and blocks:
			break
		blocks.append(block[:remaining])
		remaining -= len(block)
		if remaining <= 0:
			break
	return "\n".join(blocks)


def normalize_howto_output(task: str, generated_text: str) -> str:
	text = (generated_text or "").strip()
	if not text:
		text = "## Summary\nInsufficient generated content."
	lines: list[str] = [f"# How-To: {task.strip()}", "", text]
	normalized = "\n".join(lines).strip()
	for section in REQUIRED_SECTIONS:
		header = f"## {section}"
		if header not in normalized:
			normalized += f"\n\n{header}\nNot provided from available evidence."
	return normalized


def extract_evidence_commands(hits: List[RetrievalHit], max_commands: int = 8) -> list[str]:
	commands: list[str] = []
	seen: set[str] = set()
	for hit in hits:
		for match in EVIDENCE_COMMAND_RE.finditer(hit.content or ""):
			command = (match.group(1) or "").strip()
			if not command:
				continue
			if command in seen:
				continue
			seen.add(command)
			commands.append(command)
			if len(commands) >= max_commands:
				return commands
		for match in BACKTICK_COMMAND_RE.finditer(hit.content or ""):
			command = (match.group("cmd") or "").strip()
			if not command:
				continue
			if command in seen:
				continue
			seen.add(command)
			commands.append(command)
			if len(commands) >= max_commands:
				return commands
		for match in INLINE_COMMAND_RE.finditer(hit.content or ""):
			command = (match.group("cmd") or "").strip()
			if not command:
				continue
			if command in seen:
				continue
			seen.add(command)
			commands.append(command)
			if len(commands) >= max_commands:
				return commands
	return commands


def inject_commands_section(answer_text: str, commands: List[str]) -> str:
	if not commands:
		return answer_text
	commands_body = "\n".join(f"- `{command}`" for command in commands)
	replacement = f"## Commands\n{commands_body}\n"
	if "## Commands\n" not in answer_text:
		return answer_text + "\n\n" + replacement
	return re.sub(
		r"(?ms)^## Commands\n.*?(?=^##\s+[A-Za-z ]+\n|\Z)",
		replacement,
		answer_text,
	)


def build_howto_response(
	task: str,
	generated_text: str,
	hits: List[RetrievalHit],
	max_citations: int = 4,
	command_hits: List[RetrievalHit] | None = None,
) -> HowToResponse:
	selected = hits[:max_citations]
	citations = [build_citation(hit) for hit in selected]
	answer = normalize_howto_output(task, generated_text)
	evidence_for_commands = command_hits if command_hits is not None else hits
	answer = inject_commands_section(answer, extract_evidence_commands(evidence_for_commands, max_commands=20))
	return HowToResponse(answer=answer, citations=citations, supported=bool(selected))
