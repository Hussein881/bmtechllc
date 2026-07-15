"""Unified web interface for client and admin users.

Tag: reusable-asset

Purpose:
- Provide separate routes for Ask, How-To, Planner, Triage, and Readiness.
- Keep trust states explicit: verified, unsupported, blocked, restricted, unreviewed.
- Enforce role-based route access in the app shell (user vs admin).
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from statistics import mean, pstdev
from typing import Any
from urllib.parse import parse_qs, urlparse

from work_knowledge_agent.guardrails.human_approval import ALLOWED_TRIAGE_DISPOSITIONS
from work_knowledge_agent.workflows.curation_triage_workflow import run_curation_triage_workflow
from work_knowledge_agent.workflows.curation_workflow import CurationWorkflowConfig, run_curation_workflow
from work_knowledge_agent.workflows.howto_workflow import HowToWorkflowConfig, run_howto_workflow
from work_knowledge_agent.workflows.planning_workflow import PlanningWorkflowConfig, run_planning_workflow
from work_knowledge_agent.workflows.qa_workflow import QAWorkflowConfig, run_qa_workflow


@dataclass(frozen=True)
class PortalConfig:
	host: str
	port: int
	chunks_path: Path
	metadata_path: Path
	keyword_index_path: Path
	vector_index_path: Path
	readiness_json_path: Path
	readiness_md_path: Path
	triage_output_path: Path
	triage_history_path: Path
	qa_config: QAWorkflowConfig
	howto_config: HowToWorkflowConfig
	planning_config: PlanningWorkflowConfig
	curation_config: CurationWorkflowConfig
	default_triage_disposition: str


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Run unified client/admin web interface")
	parser.add_argument("--host", default="127.0.0.1")
	parser.add_argument("--port", type=int, default=8771)
	parser.add_argument("--chunks", type=Path, default=Path("data/processed/chunks.jsonl"))
	parser.add_argument("--metadata", type=Path, default=Path("data/processed/metadata.parquet"))
	parser.add_argument("--keyword-index", type=Path, default=Path("data/indexes/keyword/index.json"))
	parser.add_argument("--vector-index", type=Path, default=Path("data/indexes/vector/index.json"))
	parser.add_argument("--readiness-json", type=Path, default=Path("data/eval/phase6_readiness_latest.json"))
	parser.add_argument("--readiness-markdown", type=Path, default=Path("data/eval/phase6_readiness_packet.md"))
	parser.add_argument("--triage-output", type=Path, default=Path("data/eval/curation_triage_latest.json"))
	parser.add_argument("--triage-history", type=Path, default=Path("data/eval/curation_triage_history.jsonl"))
	parser.add_argument("--default-role", choices=["user", "admin"], default="user")
	parser.add_argument("--top-k", type=int, default=8)
	parser.add_argument("--allowed-confidentiality", nargs="+", default=["public", "internal", "confidential"])
	parser.add_argument("--default-disposition", choices=["accepted", "deferred", "rejected"], default="deferred")
	parser.add_argument("--provider", default="", help="Override WKA_LLM_PROVIDER (watsonx|anthropic)")
	parser.add_argument("--project-id", default="", help="Override DEBUG_AGENT_LLM_WATSONX_PROJECT_ID")
	parser.add_argument("--url", default="", help="Override DEBUG_AGENT_LLM_WATSONX_URL")
	parser.add_argument("--apikey-file", default="", help="Override DEBUG_AGENT_LLM_WATSONX_APIKEY_FILE")
	parser.add_argument("--iam-token-url", default="", help="Override DEBUG_AGENT_LLM_IAM_TOKEN_URL")
	parser.add_argument("--model-id", default="", help="Override WKA_WATSONX_MODEL_ID")
	parser.add_argument("--api-version", default="", help="Override WKA_WATSONX_API_VERSION")
	parser.add_argument("--prompt-version", default="", help="Override WKA_WATSONX_PROMPT_VERSION")
	parser.add_argument("--anthropic-model-id", default="", help="Override WKA_ANTHROPIC_MODEL_ID")
	parser.add_argument("--anthropic-apikey-file", default="", help="Override WKA_ANTHROPIC_APIKEY_FILE")
	parser.add_argument("--anthropic-api-version", default="", help="Override WKA_ANTHROPIC_API_VERSION")
	parser.add_argument("--anthropic-prompt-version", default="", help="Override WKA_ANTHROPIC_PROMPT_VERSION")
	parser.add_argument("--anthropic-base-url", default="", help="Override WKA_ANTHROPIC_BASE_URL")
	return parser.parse_args()


def _apply_override(env_key: str, value: str) -> None:
	if value.strip():
		os.environ[env_key] = value.strip()


def _load_json(path: Path) -> dict[str, Any]:
	if not path.exists():
		return {}
	text = path.read_text(encoding="utf-8").strip()
	if not text:
		return {}
	try:
		payload = json.loads(text)
		if isinstance(payload, dict):
			return payload
	except json.JSONDecodeError:
		return {}
	return {}


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


def _safe(value: Any) -> str:
	return html.escape(str(value))


def _render_inline_markdown(text: str) -> str:
	escaped = html.escape(text)
	escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
	escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
	escaped = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escaped)
	return escaped


def _markdown_to_html(markdown_text: str) -> str:
	lines = (markdown_text or "").splitlines()
	html_parts: list[str] = []
	in_code_block = False
	code_lines: list[str] = []
	in_ul = False
	in_ol = False
	paragraph_lines: list[str] = []

	def flush_paragraph() -> None:
		nonlocal paragraph_lines
		if paragraph_lines:
			joined = " ".join(part.strip() for part in paragraph_lines if part.strip())
			if joined:
				html_parts.append(f"<p>{_render_inline_markdown(joined)}</p>")
			paragraph_lines = []

	def close_lists() -> None:
		nonlocal in_ul, in_ol
		if in_ul:
			html_parts.append("</ul>")
			in_ul = False
		if in_ol:
			html_parts.append("</ol>")
			in_ol = False

	for raw_line in lines:
		line = raw_line.rstrip("\n")
		stripped = line.strip()

		if stripped.startswith("```"):
			flush_paragraph()
			close_lists()
			if in_code_block:
				code_html = html.escape("\n".join(code_lines))
				html_parts.append(f"<pre><code>{code_html}</code></pre>")
				code_lines = []
				in_code_block = False
			else:
				in_code_block = True
			continue

		if in_code_block:
			code_lines.append(line)
			continue

		if not stripped:
			flush_paragraph()
			close_lists()
			continue

		if stripped.startswith("# "):
			flush_paragraph()
			close_lists()
			html_parts.append(f"<h1>{_render_inline_markdown(stripped[2:].strip())}</h1>")
			continue

		if stripped.startswith("## "):
			flush_paragraph()
			close_lists()
			html_parts.append(f"<h2>{_render_inline_markdown(stripped[3:].strip())}</h2>")
			continue

		if stripped.startswith("### "):
			flush_paragraph()
			close_lists()
			html_parts.append(f"<h3>{_render_inline_markdown(stripped[4:].strip())}</h3>")
			continue

		unordered_match = re.match(r"^[-*]\s+(.*)$", stripped)
		if unordered_match:
			flush_paragraph()
			if in_ol:
				html_parts.append("</ol>")
				in_ol = False
			if not in_ul:
				html_parts.append("<ul>")
				in_ul = True
			html_parts.append(f"<li>{_render_inline_markdown(unordered_match.group(1).strip())}</li>")
			continue

		ordered_match = re.match(r"^(\d+)\.\s+(.*)$", stripped)
		if ordered_match:
			flush_paragraph()
			if in_ul:
				html_parts.append("</ul>")
				in_ul = False
			if not in_ol:
				html_parts.append("<ol>")
				in_ol = True
			html_parts.append(f"<li>{_render_inline_markdown(ordered_match.group(2).strip())}</li>")
			continue

		paragraph_lines.append(stripped)

	flush_paragraph()
	close_lists()
	if in_code_block:
		code_html = html.escape("\n".join(code_lines))
		html_parts.append(f"<pre><code>{code_html}</code></pre>")

	return "\n".join(html_parts)


def _readiness_stability(report: dict[str, Any]) -> dict[str, Any]:
	result: dict[str, Any] = {}
	for key in ("howto", "planner"):
		section = report.get("quality_metrics", {}).get(key, {})
		lat = section.get("latency_p95_ms")
		if lat is None:
			continue
		result[key] = {
			"latest_latency_p95_ms": float(lat),
			"trials_per_case": int(report.get("howto_eval_provenance", {}).get("trials_per_case", 0) if key == "howto" else report.get("quality_metrics", {}).get("planner", {}).get("total_runs", 0) or 0),
		}

	# Variance estimation from per-case trial booleans where available.
	# This stays conservative and surfaces unknown when insufficient detail exists.
	for key, report_file in (("howto", Path("data/eval/howto_report_latest.json")), ("planner", Path("data/eval/plan_report_latest.json"))):
		payload = _load_json(report_file)
		trials: list[float] = []
		for case in payload.get("per_case", []):
			for trial in case.get("trials", []):
				if isinstance(trial, dict):
					trials.append(1.0 if bool(trial.get("supported", False)) else 0.0)
		if trials:
			result.setdefault(key, {})["trial_count"] = len(trials)
			result[key]["trial_mean_supported"] = round(mean(trials), 3)
			result[key]["trial_std_supported"] = round(pstdev(trials), 3) if len(trials) > 1 else 0.0
			result[key]["stability_flag"] = "unstable" if (len(trials) > 1 and pstdev(trials) > 0.15) else "stable"
		else:
			result.setdefault(key, {})["trial_count"] = 0
			result[key]["stability_flag"] = "unknown"
	return result


def _state_from_guardrails(guardrail_status: dict[str, Any]) -> str:
	before = int(guardrail_status.get("retrieval_hits_before_confidentiality", 0) or 0)
	after = int(guardrail_status.get("retrieval_hits_after_confidentiality", 0) or 0)
	if before > 0 and after == 0:
		return "restricted"
	if not bool(guardrail_status.get("output_confidentiality_ok", True)):
		return "restricted"
	if not bool(guardrail_status.get("supported", False)):
		reason = str(guardrail_status.get("citation_reason", "")).lower()
		if reason and reason not in {"missing_evidence", ""}:
			return "blocked"
		return "unsupported"
	if not bool(guardrail_status.get("citation_ok", True)):
		return "blocked"
	return "verified"


def _role_from_request(handler: BaseHTTPRequestHandler, default_role: str) -> str:
	parsed = urlparse(handler.path)
	params = parse_qs(parsed.query)
	param_role = str(params.get("role", [""])[0]).strip().lower()
	if param_role in {"user", "admin"}:
		return param_role
	header_role = str(handler.headers.get("X-WKA-Role", "")).strip().lower()
	if header_role in {"user", "admin"}:
		return header_role
	return default_role


def _route_requires_admin(path: str) -> bool:
	return path in {"/triage", "/readiness"}


def _base_css() -> str:
	return """
<style>
:root {
  --bg: #f5f7f9;
  --surface: #ffffff;
  --text: #1d2733;
  --muted: #5f6c7b;
  --line: #d9e1e8;
  --accent: #0b6b8a;
  --ok: #0f766e;
  --warn: #a16207;
  --err: #b42318;
  --neutral: #475569;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  background: var(--bg);
  color: var(--text);
}
a { color: var(--accent); text-decoration: none; }
a:focus, button:focus, input:focus, textarea:focus, select:focus, details:focus {
  outline: 3px solid #93c5fd;
  outline-offset: 2px;
}
.shell { display: grid; grid-template-columns: 260px 1fr; min-height: 100vh; }
.side {
  border-right: 1px solid var(--line);
  background: #fbfcfd;
  padding: 16px;
}
.main { padding: 20px; }
.title { margin: 0; font-size: 1.1rem; font-weight: 700; }
.muted { color: var(--muted); }
.nav-group { margin-top: 18px; }
.nav-item {
  display: block;
  padding: 8px 10px;
  border-radius: 8px;
  margin-bottom: 6px;
  border: 1px solid transparent;
}
.nav-item.active {
  background: #eaf3f7;
  border-color: #bfd8e3;
  font-weight: 600;
}
.role-badge {
  display: inline-block;
  font-size: 0.76rem;
  font-weight: 700;
  padding: 4px 8px;
  border-radius: 999px;
  border: 1px solid var(--line);
  margin-top: 10px;
}
.card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 14px;
}
.grid { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }
.h2 { margin: 0 0 8px; font-size: 1.12rem; }
.chips { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 8px; }
.chip {
  font-size: 0.75rem;
  font-weight: 700;
  border-radius: 999px;
  padding: 4px 8px;
  border: 1px solid;
}
.state-verified { color: var(--ok); border-color: #99f6e4; background: #f0fdfa; }
.state-unsupported { color: var(--warn); border-color: #fde68a; background: #fffbeb; }
.state-blocked { color: var(--err); border-color: #fecaca; background: #fef2f2; }
.state-restricted { color: #7c3aed; border-color: #ddd6fe; background: #f5f3ff; }
.state-unreviewed { color: var(--neutral); border-color: #cbd5e1; background: #f8fafc; }
.markdown-body h1,
.markdown-body h2,
.markdown-body h3 {
	margin: 0 0 0.65rem;
	line-height: 1.25;
}
.markdown-body h1 { font-size: 1.35rem; }
.markdown-body h2 { font-size: 1.15rem; margin-top: 0.95rem; }
.markdown-body h3 { font-size: 1.02rem; margin-top: 0.8rem; }
.markdown-body p { margin: 0 0 0.8rem; line-height: 1.5; }
.markdown-body ul,
.markdown-body ol { margin: 0 0 0.85rem 1.15rem; padding-left: 1rem; }
.markdown-body li { margin-bottom: 0.35rem; line-height: 1.45; }
.markdown-body code {
	background: #e2e8f0;
	border-radius: 4px;
	padding: 0.1rem 0.3rem;
	font-size: 0.9em;
}
.markdown-body pre code {
	background: transparent;
	padding: 0;
}
textarea, input[type=text], select {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 9px;
  font-size: 0.95rem;
  background: #fff;
}
textarea { min-height: 108px; resize: vertical; }
button {
  border: 1px solid #0c6280;
  border-radius: 8px;
  background: #0b6b8a;
  color: #fff;
  padding: 9px 12px;
  font-weight: 600;
  cursor: pointer;
}
button.secondary {
  color: var(--text);
  background: #fff;
  border-color: var(--line);
}
pre {
  margin: 0;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #f8fafc;
  padding: 10px;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 0.9rem;
}
.warning-banner {
  border: 1px solid #fcd34d;
  background: #fffbeb;
  color: #92400e;
  border-radius: 10px;
  padding: 10px;
  margin-bottom: 12px;
}
.error-banner {
  border: 1px solid #fecaca;
  background: #fef2f2;
  color: #991b1b;
  border-radius: 10px;
  padding: 10px;
  margin-bottom: 12px;
}
@media (max-width: 980px) {
  .shell { grid-template-columns: 1fr; }
  .side { border-right: none; border-bottom: 1px solid var(--line); }
}
@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; }
}
</style>
"""

def _render_shell(role: str, path: str, body: str, default_role: str) -> str:
	admin_links = ""
	if role == "admin":
		admin_links = (
			f'<a class="nav-item {"active" if path=="/triage" else ""}" href="/triage?role={role}">Triage</a>'
			f'<a class="nav-item {"active" if path=="/readiness" else ""}" href="/readiness?role={role}">Readiness</a>'
		)
	role_switch = ""
	if role == "admin":
		role_switch = '<a class="nav-item" href="/ask?role=user">Switch To End User View</a>'
	else:
		role_switch = '<a class="nav-item" href="/ask?role=admin">Switch To Admin View</a>'

	return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Work Knowledge Agent Portal</title>
  {_base_css()}
</head>
<body>
  <div class=\"shell\">
    <aside class=\"side\">
      <h1 class=\"title\">Work Knowledge Agent</h1>
      <p class=\"muted\">Enterprise Knowledge Interface</p>
      <span class=\"role-badge\">Role: {role}</span>
      <div class=\"nav-group\">
        <a class=\"nav-item {"active" if path=="/ask" else ""}\" href=\"/ask?role={role}\">Ask</a>
        <a class=\"nav-item {"active" if path=="/howto" else ""}\" href=\"/howto?role={role}\">How-To</a>
        <a class=\"nav-item {"active" if path=="/plan" else ""}\" href=\"/plan?role={role}\">Planner</a>
      </div>
      <div class=\"nav-group\">
        <div class=\"muted\" style=\"font-size:0.8rem;margin-bottom:6px;\">Admin / Reviewer</div>
        {admin_links}
      </div>
      <div class=\"nav-group\">{role_switch}</div>
      <div class=\"nav-group muted\" style=\"font-size:0.8rem;\">Default role: {default_role}</div>
    </aside>
    <main class=\"main\">{body}</main>
  </div>
</body>
</html>
"""


class PortalHandler(BaseHTTPRequestHandler):
	config: PortalConfig
	default_role: str

	def _send_html(self, html_text: str, status: int = 200) -> None:
		payload = html_text.encode("utf-8")
		self.send_response(status)
		self.send_header("Content-Type", "text/html; charset=utf-8")
		self.send_header("Content-Length", str(len(payload)))
		self.end_headers()
		self.wfile.write(payload)

	def _redirect(self, path: str) -> None:
		self.send_response(302)
		self.send_header("Location", path)
		self.end_headers()

	def _read_form(self) -> dict[str, list[str]]:
		length = int(self.headers.get("Content-Length", "0") or "0")
		body = self.rfile.read(length).decode("utf-8", errors="replace") if length > 0 else ""
		return parse_qs(body)

	def _full_path(self) -> tuple[str, dict[str, list[str]]]:
		parsed = urlparse(self.path)
		return parsed.path, parse_qs(parsed.query)

	def _access_denied(self, role: str, path: str) -> None:
		body = (
			'<div class="error-banner"><strong>Access Restricted.</strong> '
			'This route is available only to admin/reviewer users.</div>'
			f'<a class="nav-item" href="/ask?role={role}">Return To Ask</a>'
		)
		self._send_html(_render_shell(role, path, body, self.default_role), status=403)

	def do_GET(self) -> None:  # noqa: N802
		path, _ = self._full_path()
		if path == "/":
			self._redirect("/ask")
			return

		role = _role_from_request(self, self.default_role)
		if _route_requires_admin(path) and role != "admin":
			self._access_denied(role, path)
			return

		if path == "/ask":
			self._send_html(_render_shell(role, path, self._render_ask(role), self.default_role))
			return
		if path == "/howto":
			self._send_html(_render_shell(role, path, self._render_howto(role), self.default_role))
			return
		if path == "/plan":
			self._send_html(_render_shell(role, path, self._render_plan(role), self.default_role))
			return
		if path == "/triage":
			self._send_html(_render_shell(role, path, self._render_triage(role), self.default_role))
			return
		if path == "/readiness":
			self._send_html(_render_shell(role, path, self._render_readiness(role), self.default_role))
			return

		self._send_html(_render_shell(role, path, '<div class="error-banner">Route not found.</div>', self.default_role), status=404)

	def do_POST(self) -> None:  # noqa: N802
		path, _ = self._full_path()
		role = _role_from_request(self, self.default_role)
		if _route_requires_admin(path) and role != "admin":
			self._access_denied(role, path)
			return

		form = self._read_form()
		if path == "/ask":
			self._send_html(_render_shell(role, path, self._render_ask(role, form), self.default_role))
			return
		if path == "/howto":
			self._send_html(_render_shell(role, path, self._render_howto(role, form), self.default_role))
			return
		if path == "/plan":
			self._send_html(_render_shell(role, path, self._render_plan(role, form), self.default_role))
			return
		if path == "/triage":
			self._send_html(_render_shell(role, path, self._render_triage(role, form), self.default_role))
			return
		if path == "/readiness":
			self._send_html(_render_shell(role, path, self._render_readiness(role), self.default_role))
			return

		self._send_html(_render_shell(role, path, '<div class="error-banner">Route not found.</div>', self.default_role), status=404)

	def _render_provenance_card(self, citations: list[dict[str, Any]]) -> str:
		rows: list[str] = []
		for idx, citation in enumerate(citations, start=1):
			tier = _safe(citation.get("confidentiality_level", "internal"))
			source_file = _safe(citation.get("source_file", ""))
			section = _safe(citation.get("section_heading", ""))
			score = _safe(citation.get("retrieval_score", ""))
			excerpt = _safe(citation.get("snippet", citation.get("evidence", "")))
			rows.append(
				f'<details class="card"><summary>[{idx}] {source_file} :: {section}</summary>'
				f'<div class="chips"><span class="chip state-unreviewed">Tier: {tier}</span>'
				f'<span class="chip state-unreviewed">Score: {score}</span></div>'
				f'<pre>{excerpt}</pre></details>'
			)
		if not rows:
			return '<div class="warning-banner">No citations returned.</div>'
		return "".join(rows)

	def _render_guardrail_summary(self, guardrail_status: dict[str, Any]) -> str:
		citation_ok = bool(guardrail_status.get("citation_ok", False))
		anchor_ok = bool(guardrail_status.get("entity_anchor_ok", True))
		coverage = guardrail_status.get("query_token_coverage", 0.0)
		conf_filtered = int(guardrail_status.get("confidentiality_filtered_out", 0) or 0)
		friendly = [
			f"Citation check: {'passed' if citation_ok else 'failed'}",
			f"Entity reference alignment: {'passed' if anchor_ok else 'needs review'}",
			f"Evidence coverage: {coverage}",
			f"Confidentiality-filtered evidence count: {conf_filtered}",
		]
		return '<div class="card"><h2 class="h2">Trust Summary</h2><ul>' + "".join(f"<li>{_safe(line)}</li>" for line in friendly) + "</ul><details><summary>Technical details</summary><pre>" + _safe(json.dumps(guardrail_status, ensure_ascii=True, indent=2)) + "</pre></details></div>"

	def _render_ask(self, role: str, form: dict[str, list[str]] | None = None) -> str:
		question = ""
		result_html = ""
		if form is not None:
			question = str(form.get("question", [""])[0]).strip()
			if question:
				try:
					result = run_qa_workflow(
						question=question,
						chunks_path=self.config.chunks_path,
						metadata_path=self.config.metadata_path,
						keyword_index_path=self.config.keyword_index_path,
						vector_index_path=self.config.vector_index_path,
						config=self.config.qa_config,
					)
					state = _state_from_guardrails(result.guardrail_status)
					status_msg = {
						"verified": "Answer supported by retrieved evidence.",
						"unsupported": "No sufficient evidence found for a reliable answer.",
						"blocked": "Answer did not pass guardrail checks.",
						"restricted": "Relevant evidence exists, but your current access tier cannot view it.",
					}.get(state, "Result state unknown.")
					answer_html = _markdown_to_html(result.response.answer)
					citations_html = self._render_provenance_card(result.response.citations)
					result_html = (
						'<div class="card">'
						'<h2 class="h2">Answer</h2>'
						f'<div class="chips"><span class="chip state-{state}">{state.upper()}</span></div>'
						f'<p>{_safe(status_msg)}</p>'
						f'<article class="markdown-body">{answer_html}</article>'
						"</div>"
						+ self._render_guardrail_summary(result.guardrail_status)
						+ '<div class="card"><h2 class="h2">Citations and Provenance</h2>'
						+ citations_html
						+ "</div>"
					)
				except Exception as exc:  # noqa: BLE001
					result_html = f'<div class="error-banner">Ask execution failed: {_safe(exc)}</div>'
			else:
				result_html = '<div class="warning-banner">Enter a question to run Q&A.</div>'

		return (
			'<div class="card"><h2 class="h2">Ask</h2><p class="muted">Extractive Q&A with citation-first trust signals.</p>'
			f'<form method="post" action="/ask?role={role}">'
			f'<textarea name="question" placeholder="Ask a question...">{_safe(question)}</textarea>'
			'<div style="margin-top:10px;"><button type="submit">Submit</button></div></form></div>'
			+ result_html
		)

	def _render_howto(self, role: str, form: dict[str, list[str]] | None = None) -> str:
		task = ""
		result_html = ""
		if form is not None:
			task = str(form.get("task", [""])[0]).strip()
			show_blocked = bool(str(form.get("show_blocked", [""])[0]).strip() == "true") and role == "admin"
			if task:
				try:
					result = run_howto_workflow(
						task=task,
						chunks_path=self.config.chunks_path,
						metadata_path=self.config.metadata_path,
						keyword_index_path=self.config.keyword_index_path,
						vector_index_path=self.config.vector_index_path,
						config=self.config.howto_config,
					)
					state = _state_from_guardrails(result.guardrail_status)
					answer_visible = state in {"verified", "unsupported", "restricted"} or show_blocked
					answer_text = result.response.answer if answer_visible else "This answer did not pass the accuracy guardrail and is hidden in end-user view."
					answer_html = _markdown_to_html(answer_text)
					commands_present = "## Commands" in result.response.answer
					cmd_note = "Commands are evidence-grounded and deterministically injected from retrieved sources." if commands_present else "No command section available."
					lat = _format_duration_ms(float(result.stage_times_ms.get("total", 0.0)))
					result_html = (
						'<div class="card"><h2 class="h2">How-To Procedure</h2>'
						f'<div class="chips"><span class="chip state-{state}">{state.upper()}</span>'
						f'<span class="chip state-unreviewed">Latency: {lat}</span></div>'
						f'<article class="markdown-body">{answer_html}</article></div>'
						+ f'<div class="card"><h2 class="h2">Commands</h2><p>{_safe(cmd_note)}</p></div>'
						+ self._render_guardrail_summary(result.guardrail_status)
						+ '<div class="card"><h2 class="h2">Sources</h2>'
						+ self._render_provenance_card(result.response.citations)
						+ '</div>'
					)
					if state == "blocked" and role == "admin":
						result_html += (
							'<form method="post" action="/howto?role=admin">'
							f'<input type="hidden" name="task" value="{_safe(task)}">'
							'<input type="hidden" name="show_blocked" value="true">'
							'<button class="secondary" type="submit">Reviewer Mode: Reveal Blocked Output</button>'
							'</form>'
						)
				except Exception as exc:  # noqa: BLE001
					result_html = f'<div class="error-banner">How-To execution failed: {_safe(exc)}</div>'
			else:
				result_html = '<div class="warning-banner">Enter a task to generate a procedure.</div>'

		return (
			'<div class="card"><h2 class="h2">How-To</h2><p class="muted">Fixed-template procedures with command grounding and guardrail enforcement.</p>'
			f'<form method="post" action="/howto?role={role}">'
			f'<textarea name="task" placeholder="Describe the procedure goal...">{_safe(task)}</textarea>'
			'<div style="margin-top:10px;"><button type="submit">Generate Procedure</button></div></form></div>'
			+ result_html
		)

	def _render_plan(self, role: str, form: dict[str, list[str]] | None = None) -> str:
		goal = ""
		result_html = ""
		if form is not None:
			goal = str(form.get("goal", [""])[0]).strip()
			if goal:
				try:
					result = run_planning_workflow(
						goal=goal,
						chunks_path=self.config.chunks_path,
						metadata_path=self.config.metadata_path,
						keyword_index_path=self.config.keyword_index_path,
						vector_index_path=self.config.vector_index_path,
						config=self.config.planning_config,
					)
					state = _state_from_guardrails(result.guardrail_status)
					lat = _format_duration_ms(float(result.stage_times_ms.get("total", 0.0)))
					open_q = "## Open Questions" in result.response.answer
					answer_html = _markdown_to_html(result.response.answer)
					result_html = (
						'<div class="card"><h2 class="h2">Plan Checklist</h2>'
						f'<div class="chips"><span class="chip state-{state}">{state.upper()}</span>'
						f'<span class="chip state-unreviewed">Latency: {lat}</span></div>'
						f'<article class="markdown-body">{answer_html}</article></div>'
						+ ('<div class="warning-banner"><strong>Open Questions Present.</strong> Additional context is required before execution.</div>' if open_q else '')
						+ self._render_guardrail_summary(result.guardrail_status)
						+ '<div class="card"><h2 class="h2">Sources</h2>'
						+ self._render_provenance_card(result.response.citations)
						+ '</div>'
					)
				except Exception as exc:  # noqa: BLE001
					result_html = f'<div class="error-banner">Planner execution failed: {_safe(exc)}</div>'
			else:
				result_html = '<div class="warning-banner">Enter a goal to generate a plan.</div>'

		return (
			'<div class="card"><h2 class="h2">Planner</h2><p class="muted">Ordered tasks with dependencies, confidence markers, and open questions.</p>'
			f'<form method="post" action="/plan?role={role}">'
			f'<textarea name="goal" placeholder="Describe the planning goal...">{_safe(goal)}</textarea>'
			'<div style="margin-top:10px;"><button type="submit">Generate Plan</button></div></form></div>'
			+ result_html
		)

	def _render_triage(self, role: str, form: dict[str, list[str]] | None = None) -> str:
		topic = ""
		result_html = ""
		if form is not None:
			action = str(form.get("action", ["generate"])[0]).strip().lower()
			topic = str(form.get("topic", [""])[0]).strip()
			if topic:
				try:
					curation = run_curation_workflow(
						topic=topic,
						chunks_path=self.config.chunks_path,
						metadata_path=self.config.metadata_path,
						keyword_index_path=self.config.keyword_index_path,
						vector_index_path=self.config.vector_index_path,
						config=self.config.curation_config,
					)
					items_html = []
					decisions = []
					for idx, proposal in enumerate(curation.proposals, start=1):
						proposal_id = f"proposal-{idx:03d}"
						ptype = proposal.proposal_type
						disp = str(form.get(f"disp__{proposal_id}", [self.config.default_triage_disposition])[0]).strip().lower()
						notes = str(form.get(f"notes__{proposal_id}", [""])[0]).strip()
						reviewer = str(form.get(f"reviewer__{proposal_id}", [""])[0]).strip()
						approved = str(form.get(f"approved__{proposal_id}", [""])[0]).strip().lower() == "true"
						if disp not in ALLOWED_TRIAGE_DISPOSITIONS:
							disp = self.config.default_triage_disposition
						if disp == "accepted" and not notes:
							raise ValueError(f"Accept decision for {proposal_id} requires rationale notes.")
						evidence = _safe(json.dumps(proposal.evidence, ensure_ascii=True, indent=2))
						items_html.append(
							'<div class="card">'
							f'<h2 class="h2">{_safe(proposal_id)} | {_safe(ptype)}</h2>'
							f'<p><strong>{_safe(proposal.title)}</strong></p>'
							f'<p>{_safe(proposal.rationale)}</p>'
							'<details><summary>Evidence</summary>'
							f'<pre>{evidence}</pre></details>'
							'<label>Disposition</label>'
							f'<select name="disp__{_safe(proposal_id)}">'
							+ ''.join(
								f'<option value="{v}" {"selected" if v==disp else ""}>{v}</option>'
								for v in ("accepted", "deferred", "rejected")
							)
							+ '</select>'
							f'<label>Decision Rationale</label><textarea name="notes__{_safe(proposal_id)}">{_safe(notes)}</textarea>'
							f'<label>Reviewer</label><input type="text" name="reviewer__{_safe(proposal_id)}" value="{_safe(reviewer)}">'
							f'<label><input type="checkbox" name="approved__{_safe(proposal_id)}" value="true" {"checked" if approved else ""}> Approved</label>'
							'</div>'
						)
						decision = {"proposal_id": proposal_id, "disposition": disp, "notes": notes, "decision_timestamp_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat()}
						if reviewer or approved:
							decision["human_approval"] = {"reviewer": reviewer, "approved": approved, "notes": notes}
						decisions.append(decision)

					if action == "triage":
						triage = run_curation_triage_workflow(
							topic=topic,
							proposals=curation.proposals,
							decision_rows=decisions,
							default_disposition=self.config.default_triage_disposition,
							decision_channel="web",
						)
						payload = {
							"summary": {
								"topic": topic,
								"curation": curation.summary,
								"triage": triage.summary,
							},
							"triage": triage.to_dict(),
						}
						self.config.triage_output_path.parent.mkdir(parents=True, exist_ok=True)
						self.config.triage_output_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
						with self.config.triage_history_path.open("a", encoding="utf-8") as handle:
							event = {
								"event_type": "triage_snapshot",
								"event_timestamp_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
								"channel": "web",
								"triage_summary": triage.summary,
							}
							handle.write(json.dumps(event, ensure_ascii=True) + "\n")
						result_html = (
							'<div class="card"><h2 class="h2">Triage Saved</h2>'
							f'<pre>{_safe(json.dumps(triage.summary, ensure_ascii=True, indent=2))}</pre></div>'
						)
					else:
						result_html = (
							'<form method="post" action="/triage?role=admin">'
							'<input type="hidden" name="action" value="triage">'
							f'<input type="hidden" name="topic" value="{_safe(topic)}">'
							+ ''.join(items_html)
							+ '<button type="submit">Apply Decisions</button></form>'
						)
				except Exception as exc:  # noqa: BLE001
					result_html = f'<div class="error-banner">Triage execution failed: {_safe(exc)}</div>'
			else:
				result_html = '<div class="warning-banner">Enter a topic to generate curation proposals.</div>'

		ops = _load_json(self.config.triage_output_path)
		op_metrics = ""
		if ops:
			summary = ops.get("summary", {}).get("triage", {})
			op_metrics = (
				'<div class="card"><h2 class="h2">Operational Telemetry</h2>'
				'<p class="muted">Operational metrics only, not answer quality metrics.</p>'
				f'<pre>{_safe(json.dumps({"approval_ratio_pct": summary.get("approval_ratio_pct"), "decision_latency_ms_p50": summary.get("decision_latency_ms_p50"), "decision_latency_ms_p95": summary.get("decision_latency_ms_p95")}, ensure_ascii=True, indent=2))}</pre></div>'
			)

		return (
			'<div class="card"><h2 class="h2">Curator Triage (Admin)</h2><p class="muted">Each proposal requires explicit human disposition. Accept decisions require rationale.</p>'
			f'<form method="post" action="/triage?role={role}">'
			'<input type="hidden" name="action" value="generate">'
			f'<textarea name="topic" placeholder="Enter a topic for curation triage...">{_safe(topic)}</textarea>'
			'<div style="margin-top:10px;"><button type="submit">Generate Queue</button></div></form></div>'
			+ op_metrics
			+ result_html
		)

	def _render_readiness(self, role: str) -> str:
		report = _load_json(self.config.readiness_json_path)
		if not report:
			return '<div class="error-banner">Readiness report not found. Run phase6-readiness first.</div>'

		stability = _readiness_stability(report)
		open_conditions = report.get("carry_forward_conditions", {}).get("open_conditions", [])
		open_count = int(report.get("carry_forward_conditions", {}).get("open_condition_count", 0) or 0)
		provenance = report.get("howto_eval_provenance", {})
		review_status = str(provenance.get("review_status", "unknown"))
		review_chip = f'<span class="chip state-{"unreviewed" if review_status != "reviewed" else "verified"}">How-To Dataset: {review_status}</span>'

		warning_region = ""
		if open_count > 0:
			warning_region = '<div class="warning-banner"><strong>Open Conditions Present.</strong> Review before sign-off.<pre>' + _safe(json.dumps(open_conditions, ensure_ascii=True, indent=2)) + '</pre></div>'

		index_rec = report.get("index_evolution_recommendation", {})
		thresholds = {
			"decision": index_rec.get("decision"),
			"reason": index_rec.get("reason"),
			"observed_index_stage_total_ms": index_rec.get("observed_index_stage_total_ms"),
			"full_rebuild_warning_ms": index_rec.get("full_rebuild_warning_ms"),
			"observed_total_chunks": index_rec.get("observed_total_chunks"),
			"full_rebuild_warning_chunks": index_rec.get("full_rebuild_warning_chunks"),
		}

		metric_rows = []
		targets = {
			("qa", "refusal_accuracy_pct"): 90.0,
			("howto", "citation_ok_rate_pct"): 95.0,
			("howto", "expected_command_match_rate_pct"): 95.0,
			("planner", "expected_task_match_rate_pct"): 90.0,
			("curation", "expected_type_match_rate_pct"): 90.0,
		}
		for (phase, metric), target in targets.items():
			value = float(report.get("quality_metrics", {}).get(phase, {}).get(metric, 0.0) or 0.0)
			status = "pass" if value >= target else "fail"
			chip = "state-verified" if status == "pass" else "state-blocked"
			provenance_label = "golden-reviewed" if review_status == "reviewed" else "exploratory/unreviewed"
			metric_rows.append(
				f'<tr><td>{_safe(phase)}</td><td>{_safe(metric)}</td><td>{_safe(value)}</td><td>{_safe(target)}</td><td><span class="chip {chip}">{status}</span></td><td><span class="chip state-unreviewed">{_safe(provenance_label)}</span></td></tr>'
			)

		stability_card = '<div class="card"><h2 class="h2">Run Stability</h2><pre>' + _safe(json.dumps(stability, ensure_ascii=True, indent=2)) + '</pre></div>'
		parity = report.get("interface_parity", {})
		if not bool(parity.get("checked", False)):
			warning_region += '<div class="warning-banner"><strong>Interface parity check not executed.</strong> Health/readiness parity alone is insufficient for guardrail parity sign-off.</div>'

		md_packet = self.config.readiness_md_path.read_text(encoding="utf-8") if self.config.readiness_md_path.exists() else "Readiness markdown packet not found."
		md_packet_html = _markdown_to_html(md_packet)

		return (
			'<div class="card"><h2 class="h2">Readiness Dashboard (Admin)</h2><p class="muted">Metrics are shown with thresholds, pass/fail state, and dataset provenance.</p>'
			f'<div class="chips">{review_chip}<span class="chip state-unreviewed">Open Conditions: {_safe(open_count)}</span></div></div>'
			+ warning_region
			+ '<div class="card"><h2 class="h2">Per-Phase Metrics</h2>'
			+ '<table style="width:100%;border-collapse:collapse;"><thead><tr><th align="left">Phase</th><th align="left">Metric</th><th align="left">Value</th><th align="left">Target</th><th align="left">Status</th><th align="left">Dataset</th></tr></thead><tbody>'
			+ ''.join(metric_rows)
			+ '</tbody></table></div>'
			+ '<div class="card"><h2 class="h2">Index Strategy Recommendation</h2><pre>' + _safe(json.dumps(thresholds, ensure_ascii=True, indent=2)) + '</pre></div>'
			+ '<div class="card"><h2 class="h2">Interface Parity</h2><pre>' + _safe(json.dumps(parity, ensure_ascii=True, indent=2)) + '</pre></div>'
			+ stability_card
			+ '<div class="card"><h2 class="h2">Source Packet (Markdown View)</h2><article class="markdown-body">' + md_packet_html + '</article></div>'
		)

	def log_message(self, format: str, *args: object) -> None:  # noqa: A003
		return


def main() -> None:
	args = parse_args()
	_apply_override("WKA_LLM_PROVIDER", args.provider)
	_apply_override("DEBUG_AGENT_LLM_WATSONX_PROJECT_ID", args.project_id)
	_apply_override("DEBUG_AGENT_LLM_WATSONX_URL", args.url)
	_apply_override("DEBUG_AGENT_LLM_WATSONX_APIKEY_FILE", args.apikey_file)
	_apply_override("DEBUG_AGENT_LLM_IAM_TOKEN_URL", args.iam_token_url)
	_apply_override("WKA_WATSONX_MODEL_ID", args.model_id)
	_apply_override("WKA_WATSONX_API_VERSION", args.api_version)
	_apply_override("WKA_WATSONX_PROMPT_VERSION", args.prompt_version)
	_apply_override("WKA_ANTHROPIC_MODEL_ID", args.anthropic_model_id)
	_apply_override("WKA_ANTHROPIC_APIKEY_FILE", args.anthropic_apikey_file)
	_apply_override("WKA_ANTHROPIC_API_VERSION", args.anthropic_api_version)
	_apply_override("WKA_ANTHROPIC_PROMPT_VERSION", args.anthropic_prompt_version)
	_apply_override("WKA_ANTHROPIC_BASE_URL", args.anthropic_base_url)
	allowed_conf = tuple(args.allowed_confidentiality)
	cfg = PortalConfig(
		host=args.host,
		port=args.port,
		chunks_path=args.chunks,
		metadata_path=args.metadata,
		keyword_index_path=args.keyword_index,
		vector_index_path=args.vector_index,
		readiness_json_path=args.readiness_json,
		readiness_md_path=args.readiness_markdown,
		triage_output_path=args.triage_output,
		triage_history_path=args.triage_history,
		qa_config=QAWorkflowConfig(top_k=args.top_k, allowed_confidentiality=allowed_conf),
		howto_config=HowToWorkflowConfig(top_k=max(args.top_k, 8), allowed_confidentiality=allowed_conf),
		planning_config=PlanningWorkflowConfig(top_k=max(args.top_k, 8), allowed_confidentiality=allowed_conf),
		curation_config=CurationWorkflowConfig(top_k=max(args.top_k, 12), allowed_confidentiality=allowed_conf),
		default_triage_disposition=args.default_disposition,
	)

	handler = PortalHandler
	handler.config = cfg
	handler.default_role = args.default_role

	server = ThreadingHTTPServer((cfg.host, cfg.port), handler)
	print(f"Unified portal running at http://{cfg.host}:{cfg.port}")
	print("Routes: /ask /howto /plan /triage /readiness")
	print("Use ?role=user or ?role=admin to switch role views.")
	print("Press Ctrl+C to stop.")
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		pass
	finally:
		server.server_close()


if __name__ == "__main__":
	main()
