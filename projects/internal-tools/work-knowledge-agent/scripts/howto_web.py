"""Tool: howto_web

Tag: reusable-asset

What this tool does:
- Starts a lightweight local web server for interactive Phase 3 How-To testing.
- Renders a task input box in the browser, accepts submitted procedures, and displays
  structured how-to output, citations, guardrail status, generation metadata, and timings.
- Reuses the Phase 3 How-To workflow and Watsonx-backed generation path.

Inputs:
- Optional server host/port.
- Paths to chunks, metadata, keyword index, and vector index artifacts.
- Retrieval controls and optional Watsonx overrides.

Outputs:
- Browser-rendered How-To page with task input and result diagnostics.

Status:
- Phase 3 user testing interface.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

from work_knowledge_agent.workflows.howto_workflow import HowToWorkflowConfig, run_howto_workflow


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
	parser = argparse.ArgumentParser(description="Start a local browser How-To interface.")
	parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind")
	parser.add_argument("--port", type=int, default=8766, help="Port to listen on")
	parser.add_argument("--chunks", type=Path, default=Path("data/processed/chunks.jsonl"))
	parser.add_argument("--metadata", type=Path, default=Path("data/processed/metadata.parquet"))
	parser.add_argument("--keyword-index", type=Path, default=Path("data/indexes/keyword/index.json"))
	parser.add_argument("--vector-index", type=Path, default=Path("data/indexes/vector/index.json"))
	parser.add_argument("--top-k", type=int, default=8)
	parser.add_argument("--min-metadata-confidence", type=float, default=0.30)
	parser.add_argument(
		"--allowed-confidentiality",
		nargs="+",
		default=["public", "internal", "confidential"],
		help="Allowed confidentiality levels",
	)
	parser.add_argument("--temperature", type=float, default=0.0)
	parser.add_argument("--max-output-tokens", type=int, default=700)
	parser.add_argument("--project-id", default="", help="Override DEBUG_AGENT_LLM_WATSONX_PROJECT_ID")
	parser.add_argument("--url", default="", help="Override DEBUG_AGENT_LLM_WATSONX_URL")
	parser.add_argument("--apikey-file", default="", help="Override DEBUG_AGENT_LLM_WATSONX_APIKEY_FILE")
	parser.add_argument("--iam-token-url", default="", help="Override DEBUG_AGENT_LLM_IAM_TOKEN_URL")
	parser.add_argument("--model-id", default="", help="Override WKA_WATSONX_MODEL_ID")
	parser.add_argument("--api-version", default="", help="Override WKA_WATSONX_API_VERSION")
	parser.add_argument("--prompt-version", default="", help="Override WKA_WATSONX_PROMPT_VERSION")
	return parser.parse_args()


def _apply_override(env_key: str, value: str) -> None:
	if value.strip():
		os.environ[env_key] = value.strip()


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


def _friendly_error_message(exc: Exception) -> str:
	message = str(exc)
	if "HTTP 429" in message or "consumption_limit_reached" in message:
		return (
			"Watsonx is rate-limiting requests for the current model right now. "
			"Wait a short time and retry. If this keeps happening, reduce concurrent use of the model, "
			"shorten the task, or try again later when account load is lower.\n\n"
			f"Provider details: {message}"
		)
	if "after retries" in message:
		return (
			"The How-To generation request exhausted its retry budget. "
			"Retry in a few seconds.\n\n"
			f"Provider details: {message}"
		)
	return f"{type(exc).__name__}: {message}"


def _render_html(task: str, result: dict[str, Any] | None, error: str | None) -> str:
	safe_task = html.escape(task)
	result_block = ""

	if error:
		result_block = (
			'<section class="card error"><h2>Execution Error</h2>'
			f"<pre>{html.escape(error)}</pre></section>"
		)

	if result:
		answer_markdown = str(result.get("answer", ""))
		answer_html = _markdown_to_html(answer_markdown)
		answer_text = html.escape(answer_markdown)
		supported = html.escape(str(result.get("supported", False)).lower())
		hit_count = html.escape(str(result.get("retrieval_hit_count", 0)))
		guardrail_json = html.escape(json.dumps(result.get("guardrail_status", {}), indent=2, ensure_ascii=True))
		citations_json = html.escape(json.dumps(result.get("citations", []), indent=2, ensure_ascii=True))
		generation_json = html.escape(json.dumps(result.get("generation_metadata", {}), indent=2, ensure_ascii=True))

		times = result.get("stage_times_ms", {})
		stage_lines = []
		for stage_name, duration in times.items():
			stage_lines.append(f"{stage_name}: {_format_duration_ms(float(duration))} ({duration} ms)")
		stage_metrics = html.escape("\n".join(stage_lines))

		result_block = (
			'<section class="card"><h2>How-To Output</h2>'
			f'<article class="markdown-body">{answer_html}</article>'
			"</section>"
			'<section class="card"><h3>Raw Markdown</h3>'
			f"<pre>{answer_text}</pre>"
			"</section>"
			'<section class="grid">'
			'<div class="card small"><h3>Supported</h3>'
			f"<pre>{supported}</pre></div>"
			'<div class="card small"><h3>Retrieval Hits</h3>'
			f"<pre>{hit_count}</pre></div>"
			'<div class="card"><h3>Stage Times</h3>'
			f"<pre>{stage_metrics}</pre></div>"
			'<div class="card"><h3>Guardrail Status</h3>'
			f"<pre>{guardrail_json}</pre></div>"
			'<div class="card"><h3>Generation Metadata</h3>'
			f"<pre>{generation_json}</pre></div>"
			'<div class="card"><h3>Citations</h3>'
			f"<pre>{citations_json}</pre></div>"
			"</section>"
		)

	return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Work Knowledge Agent How-To</title>
  <style>
    :root {{
      --bg: #f3f5f8;
      --card: #ffffff;
      --text: #1c2430;
      --muted: #55606e;
      --accent: #006b5f;
      --border: #d7dee7;
      --error: #b42318;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: linear-gradient(180deg, #f7f9fb 0%, var(--bg) 100%);
      color: var(--text);
    }}
    .shell {{ max-width: 1100px; margin: 0 auto; padding: 24px; }}
    .title {{ margin: 0 0 8px; font-size: 1.6rem; }}
    .subtitle {{ margin: 0 0 18px; color: var(--muted); }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px;
      margin-bottom: 14px;
      box-shadow: 0 2px 8px rgba(16, 24, 20, 0.04);
    }}
    .small {{ min-height: 120px; }}
    .error {{ border-color: #f3c4be; color: var(--error); }}
    textarea {{
      width: 100%;
      min-height: 120px;
      padding: 10px;
      border-radius: 10px;
      border: 1px solid var(--border);
      font-size: 1rem;
      resize: vertical;
      background: #fcfdfc;
    }}
    button {{
      margin-top: 10px;
      border: none;
      border-radius: 10px;
      padding: 10px 16px;
      background: var(--accent);
      color: #fff;
      font-weight: 600;
      cursor: pointer;
    }}
    button:hover {{ filter: brightness(1.05); }}
    pre {{
      white-space: pre-wrap;
      word-break: break-word;
      margin: 0;
      background: #f8fbf8;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px;
      font-size: 0.92rem;
      line-height: 1.45;
    }}
		code {{
			background: #eef4ef;
			border-radius: 4px;
			padding: 0.1rem 0.35rem;
			font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
			font-size: 0.92em;
		}}
		.markdown-body h1,
		.markdown-body h2,
		.markdown-body h3 {{
			margin: 0 0 0.65rem;
			line-height: 1.25;
		}}
		.markdown-body h1 {{ font-size: 1.45rem; }}
		.markdown-body h2 {{ font-size: 1.2rem; margin-top: 1rem; }}
		.markdown-body h3 {{ font-size: 1.05rem; margin-top: 0.85rem; }}
		.markdown-body p {{ margin: 0 0 0.8rem; line-height: 1.55; }}
		.markdown-body ul,
		.markdown-body ol {{ margin: 0 0 0.9rem 1.25rem; padding-left: 1rem; }}
		.markdown-body li {{ margin-bottom: 0.35rem; line-height: 1.5; }}
		.markdown-body pre {{ margin: 0 0 0.9rem; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 12px; }}
  </style>
</head>
<body>
  <main class=\"shell\">
    <h1 class=\"title\">Work Knowledge Agent: How-To Test Console</h1>
    <p class=\"subtitle\">Submit a task to test the Phase 3 How-To workflow, citations, and generation diagnostics.</p>
    <section class=\"card\">
      <form method=\"post\">
        <label for=\"task\">Task</label>
        <textarea id=\"task\" name=\"task\" placeholder=\"Describe the procedure you want generated...\">{safe_task}</textarea>
        <button type=\"submit\">Generate How-To</button>
      </form>
    </section>
    {result_block}
  </main>
</body>
</html>
"""


class HowToWebHandler(BaseHTTPRequestHandler):
	chunks_path: Path
	metadata_path: Path
	keyword_index_path: Path
	vector_index_path: Path
	config: HowToWorkflowConfig
	request_lock = threading.Lock()

	def _send_page(self, task: str = "", result: dict[str, Any] | None = None, error: str | None = None) -> None:
		content = _render_html(task=task, result=result, error=error).encode("utf-8")
		self.send_response(200)
		self.send_header("Content-Type", "text/html; charset=utf-8")
		self.send_header("Content-Length", str(len(content)))
		self.end_headers()
		self.wfile.write(content)

	def do_GET(self) -> None:  # noqa: N802
		self._send_page()

	def do_POST(self) -> None:  # noqa: N802
		content_length = int(self.headers.get("Content-Length", "0"))
		body = self.rfile.read(content_length).decode("utf-8", errors="replace")
		data = parse_qs(body)
		task = data.get("task", [""])[0].strip()

		if not task:
			self._send_page(task=task, error="Please enter a task before submitting.")
			return

		if not self.request_lock.acquire(blocking=False):
			self._send_page(
				task=task,
				error=(
					"A How-To generation request is already running in this local test console. "
					"Wait for it to finish, then submit again."
				),
			)
			return

		try:
			workflow_result = run_howto_workflow(
				task=task,
				chunks_path=self.chunks_path,
				metadata_path=self.metadata_path,
				keyword_index_path=self.keyword_index_path,
				vector_index_path=self.vector_index_path,
				config=self.config,
			)
			result_payload = {
				"answer": workflow_result.response.answer,
				"supported": workflow_result.response.supported,
				"citations": workflow_result.response.citations,
				"guardrail_status": workflow_result.guardrail_status,
				"stage_times_ms": workflow_result.stage_times_ms,
				"generation_metadata": workflow_result.generation_metadata,
				"retrieval_hit_count": len(workflow_result.retrieval_hits),
			}
			self._send_page(task=task, result=result_payload)
		except Exception as exc:  # noqa: BLE001
			self._send_page(task=task, error=_friendly_error_message(exc))
		finally:
			self.request_lock.release()

	def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
		return


def main() -> None:
	args = parse_args()
	_apply_override("DEBUG_AGENT_LLM_WATSONX_PROJECT_ID", args.project_id)
	_apply_override("DEBUG_AGENT_LLM_WATSONX_URL", args.url)
	_apply_override("DEBUG_AGENT_LLM_WATSONX_APIKEY_FILE", args.apikey_file)
	_apply_override("DEBUG_AGENT_LLM_IAM_TOKEN_URL", args.iam_token_url)
	_apply_override("WKA_WATSONX_MODEL_ID", args.model_id)
	_apply_override("WKA_WATSONX_API_VERSION", args.api_version)
	_apply_override("WKA_WATSONX_PROMPT_VERSION", args.prompt_version)

	handler_cls = HowToWebHandler
	handler_cls.chunks_path = args.chunks
	handler_cls.metadata_path = args.metadata
	handler_cls.keyword_index_path = args.keyword_index
	handler_cls.vector_index_path = args.vector_index
	handler_cls.config = HowToWorkflowConfig(
		top_k=args.top_k,
		min_metadata_confidence=args.min_metadata_confidence,
		allowed_confidentiality=tuple(args.allowed_confidentiality),
		temperature=args.temperature,
		max_output_tokens=args.max_output_tokens,
	)

	server = ThreadingHTTPServer((args.host, args.port), handler_cls)
	print(f"How-To web console running at http://{args.host}:{args.port}")
	print("Press Ctrl+C to stop.")
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		pass
	finally:
		server.server_close()


if __name__ == "__main__":
	main()