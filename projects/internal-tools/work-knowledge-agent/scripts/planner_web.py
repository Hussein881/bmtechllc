"""Tool: planner_web

Tag: reusable-asset

What this tool does:
- Starts a lightweight local web server for interactive Phase 4 Planner testing.
- Renders a goal input box in the browser and displays planner output,
  support/citation guardrail status, citations, generation metadata, and timings.
- Reuses the Phase 4 planning workflow and Watsonx-backed generation path.

Inputs:
- Optional server host/port.
- Paths to chunks, metadata, keyword index, and vector index artifacts.
- Retrieval controls and optional Watsonx overrides.

Outputs:
- Browser-rendered Planner page with goal input and result diagnostics.

Status:
- Phase 4 user testing interface.
"""

from __future__ import annotations

import argparse
import html
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

from work_knowledge_agent.workflows.planning_workflow import PlanningWorkflowConfig, run_planning_workflow


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
	parser = argparse.ArgumentParser(description="Start a local browser Planner interface.")
	parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind")
	parser.add_argument("--port", type=int, default=8767, help="Port to listen on")
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


def _render_html(goal: str, result: dict[str, Any] | None, error: str | None) -> str:
	safe_goal = html.escape(goal)
	result_block = ""

	if error:
		result_block = (
			'<section class="card error"><h2>Execution Error</h2>'
			f"<pre>{html.escape(error)}</pre></section>"
		)

	if result:
		answer_text = html.escape(str(result.get("answer", "")))
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
			'<section class="card"><h2>Planner Output</h2>'
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
  <title>Work Knowledge Agent Planner</title>
  <style>
    :root {{
      --bg: #f1f6f5;
      --card: #ffffff;
      --text: #172422;
      --muted: #4f625d;
      --accent: #0a7f69;
      --border: #d3e3df;
      --error: #b42318;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: linear-gradient(180deg, #f8fbfa 0%, var(--bg) 100%);
      color: var(--text);
    }}
    .shell {{ max-width: 1080px; margin: 0 auto; padding: 24px; }}
    .title {{ margin: 0 0 8px; font-size: 1.65rem; }}
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
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; }}
  </style>
</head>
<body>
  <main class=\"shell\">
    <h1 class=\"title\">Work Knowledge Agent: Planner Test Console</h1>
    <p class=\"subtitle\">This UI executes the Phase 4 planning workflow.</p>
    <section class=\"card\">
      <form method=\"post\">
        <label for=\"goal\">Planning Goal</label>
        <textarea id=\"goal\" name=\"goal\" placeholder=\"Enter a planning goal...\">{safe_goal}</textarea>
        <button type=\"submit\">Generate Plan</button>
      </form>
    </section>
    {result_block}
  </main>
</body>
</html>
"""


class PlannerWebHandler(BaseHTTPRequestHandler):
	chunks_path: Path
	metadata_path: Path
	keyword_index_path: Path
	vector_index_path: Path
	config: PlanningWorkflowConfig

	def _send_page(self, goal: str = "", result: dict[str, Any] | None = None, error: str | None = None) -> None:
		content = _render_html(goal=goal, result=result, error=error).encode("utf-8")
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
		goal = data.get("goal", [""])[0].strip()

		if not goal:
			self._send_page(goal=goal, error="Please enter a planning goal before submitting.")
			return

		try:
			workflow_result = run_planning_workflow(
				goal=goal,
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
				"generation_metadata": workflow_result.generation_metadata,
				"stage_times_ms": workflow_result.stage_times_ms,
				"retrieval_hit_count": len(workflow_result.retrieval_hits),
			}
			self._send_page(goal=goal, result=result_payload)
		except Exception as exc:  # noqa: BLE001
			self._send_page(goal=goal, error=f"{type(exc).__name__}: {exc}")

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

	handler_cls = PlannerWebHandler
	handler_cls.chunks_path = args.chunks
	handler_cls.metadata_path = args.metadata
	handler_cls.keyword_index_path = args.keyword_index
	handler_cls.vector_index_path = args.vector_index
	handler_cls.config = PlanningWorkflowConfig(
		top_k=args.top_k,
		min_metadata_confidence=args.min_metadata_confidence,
		allowed_confidentiality=tuple(args.allowed_confidentiality),
		temperature=args.temperature,
		max_output_tokens=args.max_output_tokens,
	)

	server = ThreadingHTTPServer((args.host, args.port), handler_cls)
	print(f"Planner web console running at http://{args.host}:{args.port}")
	print("Press Ctrl+C to stop.")
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		pass
	finally:
		server.server_close()


if __name__ == "__main__":
	main()
