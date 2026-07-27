"""Structured planner agent helpers for Phase 4."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from work_knowledge_agent.agents.qa_agent import build_citation
from work_knowledge_agent.retrieval.hybrid_retriever import RetrievalHit

REQUIRED_SECTIONS: tuple[str, ...] = (
	"Summary",
	"Objectives",
	"Ordered Tasks",
	"Dependencies",
	"Open Questions",
	"Risks and Unknowns",
	"Sources",
)


@dataclass(frozen=True)
class PlannerResponse:
	answer: str
	citations: List[dict]
	supported: bool


def build_planner_prompt(goal: str) -> str:
	return (
		"You are generating a grounded engineering plan from retrieved evidence only.\n"
		"Use only the supplied retrieved context. Do not invent dependencies, tasks, systems, or missing context.\n"
		"Be concise and explicit. Prefer short bullet points and numbered tasks.\n"
		"Prioritize evidence that is directly relevant to the goal and ignore unrelated retrieved fragments.\n"
		"When evidence is weak, place that gap in Open Questions or Risks and Unknowns.\n"
		"In Ordered Tasks, output 3-7 one-line numbered tasks and start each task with an action verb such as Identify, Validate, Execute, Run, Monitor, or Review.\n"
		"For safe rollout goals, include tasks that identify prerequisites/systems, validate current state/access, and execute or monitor the change safely.\n"
		"For rollout or production-impacting goals, include explicit go/no-go stop criteria and rollback trigger/action criteria.\n"
		"When evidence includes concrete checks or commands, prefer those checks in Ordered Tasks instead of abstract wording.\n"
		"Return markdown using these exact section headers in this exact order:\n"
		"## Summary\n"
		"## Objectives\n"
		"## Ordered Tasks\n"
		"## Dependencies\n"
		"## Open Questions\n"
		"## Risks and Unknowns\n"
		"## Sources\n\n"
		f"Goal: {goal.strip()}"
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


def normalize_planner_output(goal: str, generated_text: str) -> str:
	text = (generated_text or "").strip()
	if not text:
		text = "## Summary\nInsufficient generated content."
	lines: list[str] = [f"# Plan: {goal.strip()}", "", text]
	normalized = "\n".join(lines).strip()
	for section in REQUIRED_SECTIONS:
		header = f"## {section}"
		if header not in normalized:
			normalized += f"\n\n{header}\nNot provided from available evidence."
	return _ensure_rollout_task_coverage(goal, normalized)


def _ensure_rollout_task_coverage(goal: str, normalized_text: str) -> str:
	goal_l = (goal or "").lower()
	if "## Ordered Tasks" not in normalized_text:
		return normalized_text

	if not any(token in goal_l for token in ("rollout", "restart", "linux", "disk", "log", "cleanup")):
		return normalized_text

	ordered_block = _extract_section_text(normalized_text, "Ordered Tasks")
	if not ordered_block:
		return normalized_text

	existing_tasks = _extract_numbered_task_lines(ordered_block)
	existing_blob = " ".join(existing_tasks).lower()
	prepend_tasks: list[str] = []

	if any(token in goal_l for token in ("linux", "disk", "log", "cleanup", "pressure")):
		if not any(token in existing_blob for token in ("affected", "system", "host", "node")):
			prepend_tasks.append("Identify affected systems and services impacted by log growth.")
		if not any(token in existing_blob for token in ("disk", "storage", "pressure", "usage", "df", "du")):
			prepend_tasks.append("Validate current disk pressure and log usage before changes using baseline checks (for example df, du, and journal/log review).")
		if not any(token in existing_blob for token in ("cleanup", "monitor", "journalctl", "logrotate", "retention")):
			prepend_tasks.append("Run cleanup or monitoring steps and verify impact safely.")
		if not any(token in existing_blob for token in ("rollback", "backout", "revert", "no-go", "stop criteria", "abort")):
			prepend_tasks.append("Define go/no-go stop criteria and rollback triggers before production rollout.")
	else:
		if not any(token in existing_blob for token in ("prerequisite", "requirement", "precheck")):
			prepend_tasks.append("Identify prerequisites and impacted systems before rollout.")
		if not any(token in existing_blob for token in ("access", "permission", "authorize", "credential", "status", "validate")):
			prepend_tasks.append("Validate current state and required access before execution.")
		if not any(token in existing_blob for token in ("execute", "run", "apply", "restart", "rollout", "monitor")):
			prepend_tasks.append("Execute the approved change and monitor immediate outcomes.")
		if not any(token in existing_blob for token in ("rollback", "backout", "revert", "no-go", "stop criteria", "abort")):
			prepend_tasks.append("Define explicit stop criteria and rollback actions before broad rollout.")

	if not prepend_tasks:
		return normalized_text

	combined = prepend_tasks + existing_tasks
	renumbered = [f"{idx}. {task}" for idx, task in enumerate(combined, start=1)]
	new_ordered_block = "\n".join(renumbered)
	return _replace_section_text(normalized_text, "Ordered Tasks", new_ordered_block)


def _extract_numbered_task_lines(section_text: str) -> list[str]:
	tasks: list[str] = []
	for line in (section_text or "").splitlines():
		value = line.strip()
		if not value:
			continue
		if value.startswith(("-", "*")):
			value = value[1:].strip()
		if value and value[0].isdigit():
			parts = value.split(".", 1)
			if len(parts) == 2 and parts[0].isdigit():
				value = parts[1].strip()
		tasks.append(value)
	return tasks


def _extract_section_text(text: str, section_name: str) -> str:
	header = f"## {section_name}"
	if header not in text:
		return ""
	after = text.split(header, 1)[1]
	next_header = "\n## "
	idx = after.find(next_header)
	if idx >= 0:
		after = after[:idx]
	return after.strip("\n")


def _replace_section_text(text: str, section_name: str, new_body: str) -> str:
	header = f"## {section_name}"
	if header not in text:
		return text
	prefix, suffix = text.split(header, 1)
	next_header = "\n## "
	idx = suffix.find(next_header)
	if idx >= 0:
		remaining = suffix[idx:]
	else:
		remaining = ""
	return f"{prefix}{header}\n{new_body}{remaining}".strip()


def build_planner_response(goal: str, generated_text: str, hits: List[RetrievalHit], max_citations: int = 4) -> PlannerResponse:
	selected = hits[:max_citations]
	citations = [build_citation(hit) for hit in selected]
	answer = normalize_planner_output(goal, generated_text)
	return PlannerResponse(answer=answer, citations=citations, supported=bool(selected))
