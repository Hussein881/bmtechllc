"""Tool: ask_web

Tag: reusable-asset

What this tool does:
- Starts a lightweight local web server for interactive Q&A testing.
- Renders a prompt box in the browser, accepts submitted questions, and displays
  answer, support status, citations, and stage timing metrics.
- Reuses the Phase 2 citation-first QA workflow and guardrails.

Inputs:
- Optional server host/port.
- Paths to chunks, metadata, keyword index, and vector index artifacts.
- Retrieval controls (top_k, confidence threshold, allowed confidentiality levels).

Outputs:
- Browser-rendered Q&A page with prompt box and result details.

Status:
- Phase 2 user testing interface.
"""

from __future__ import annotations

import argparse
import html
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

from work_knowledge_agent.workflows.qa_workflow import QAWorkflowConfig, run_qa_workflow


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
    parser = argparse.ArgumentParser(description="Start a local browser Q&A interface.")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind")
    parser.add_argument("--port", type=int, default=8765, help="Port to listen on")
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
    return parser.parse_args()


def _render_html(question: str, result: dict[str, Any] | None, error: str | None) -> str:
    safe_question = html.escape(question)
    answer_block = ""

    if error:
        answer_block = (
            '<section class="card error"><h2>Execution Error</h2>'
            f"<pre>{html.escape(error)}</pre></section>"
        )

    if result:
        answer_text = html.escape(result.get("answer", ""))
        supported = html.escape(str(result.get("supported", False)).lower())
        hit_count = html.escape(str(result.get("retrieval_hit_count", 0)))
        guardrail_json = html.escape(json.dumps(result.get("guardrail_status", {}), indent=2, ensure_ascii=True))
        citations_json = html.escape(json.dumps(result.get("citations", []), indent=2, ensure_ascii=True))

        times = result.get("stage_times_ms", {})
        stage_lines = []
        for stage_name, duration in times.items():
            stage_lines.append(f"{stage_name}: {_format_duration_ms(float(duration))} ({duration} ms)")
        stage_metrics = html.escape("\n".join(stage_lines))

        answer_block = (
            '<section class="card"><h2>Answer</h2>'
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
            '<div class="card"><h3>Citations</h3>'
            f"<pre>{citations_json}</pre></div>"
            "</section>"
        )

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Work Knowledge Agent Q&A</title>
  <style>
    :root {{
      --bg: #f4f7f2;
      --card: #ffffff;
      --text: #1f2a21;
      --muted: #55635a;
      --accent: #1a7f5a;
      --border: #dbe5dc;
      --error: #b42318;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: linear-gradient(180deg, #f7faf7 0%, var(--bg) 100%);
      color: var(--text);
    }}
    .shell {{ max-width: 1040px; margin: 0 auto; padding: 24px; }}
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
      min-height: 110px;
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
    <h1 class=\"title\">Work Knowledge Agent: Q&A Test Console</h1>
    <p class=\"subtitle\">Submit a question to test quality, citations, and guardrails.</p>
    <section class=\"card\">
      <form method=\"post\">
        <label for=\"question\">Question</label>
        <textarea id=\"question\" name=\"question\" placeholder=\"Ask a question...\">{safe_question}</textarea>
        <button type=\"submit\">Submit</button>
      </form>
    </section>
    {answer_block}
  </main>
</body>
</html>
"""


class QAWebHandler(BaseHTTPRequestHandler):
    chunks_path: Path
    metadata_path: Path
    keyword_index_path: Path
    vector_index_path: Path
    config: QAWorkflowConfig

    def _send_page(self, question: str = "", result: dict[str, Any] | None = None, error: str | None = None) -> None:
        content = _render_html(question=question, result=result, error=error).encode("utf-8")
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
        question = data.get("question", [""])[0].strip()

        if not question:
            self._send_page(question=question, error="Please enter a question before submitting.")
            return

        try:
            workflow_result = run_qa_workflow(
                question=question,
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
                "retrieval_hit_count": len(workflow_result.retrieval_hits),
            }
            self._send_page(question=question, result=result_payload)
        except Exception as exc:  # noqa: BLE001
            self._send_page(question=question, error=f"{type(exc).__name__}: {exc}")

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return


def main() -> None:
    args = parse_args()

    handler_cls = QAWebHandler
    handler_cls.chunks_path = args.chunks
    handler_cls.metadata_path = args.metadata
    handler_cls.keyword_index_path = args.keyword_index
    handler_cls.vector_index_path = args.vector_index
    handler_cls.config = QAWorkflowConfig(
        top_k=args.top_k,
        min_metadata_confidence=args.min_metadata_confidence,
        allowed_confidentiality=tuple(args.allowed_confidentiality),
    )

    server = ThreadingHTTPServer((args.host, args.port), handler_cls)
    print(f"Q&A web console running at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
