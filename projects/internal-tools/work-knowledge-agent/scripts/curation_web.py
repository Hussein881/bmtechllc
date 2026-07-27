"""Tool: curation_web

Tag: reusable-asset

What this tool does:
- Starts a local browser interface for Phase 5 curator review.
- Generates curation proposals from a topic and lets reviewers triage each item.
- Enforces human-approval checks for accepted proposals via triage workflow guardrails.
- Persists triage output to a JSON artifact path.

Inputs:
- Optional server host/port.
- Retrieval/index artifact paths and curation controls.
- Topic text and per-proposal triage decisions entered in the browser.

Outputs:
- Browser-rendered curator review page with proposal evidence and triage controls.
- Persisted triage artifact (`data/eval/curation_triage_latest.json` by default).

Status:
- Phase 5 browser review surface.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import html
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

from work_knowledge_agent.guardrails.human_approval import ALLOWED_TRIAGE_DISPOSITIONS
from work_knowledge_agent.workflows.curation_triage_workflow import run_curation_triage_workflow
from work_knowledge_agent.workflows.curation_workflow import CurationWorkflowConfig, run_curation_workflow


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
	parser = argparse.ArgumentParser(description="Start a local browser curator review interface.")
	parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind")
	parser.add_argument("--port", type=int, default=8768, help="Port to listen on")
	parser.add_argument("--chunks", type=Path, default=Path("data/processed/chunks.jsonl"))
	parser.add_argument("--metadata", type=Path, default=Path("data/processed/metadata.parquet"))
	parser.add_argument("--keyword-index", type=Path, default=Path("data/indexes/keyword/index.json"))
	parser.add_argument("--vector-index", type=Path, default=Path("data/indexes/vector/index.json"))
	parser.add_argument("--top-k", type=int, default=12)
	parser.add_argument("--min-metadata-confidence", type=float, default=0.30)
	parser.add_argument("--duplicate-similarity-threshold", type=float, default=0.92)
	parser.add_argument("--outdated-year-cutoff", type=int, default=2021)
	parser.add_argument(
		"--allowed-confidentiality",
		nargs="+",
		default=["public", "internal", "confidential"],
		help="Allowed confidentiality levels",
	)
	parser.add_argument("--min-query-token-coverage", type=float, default=0.40)
	parser.add_argument("--default-disposition", choices=["accepted", "deferred", "rejected"], default="deferred")
	parser.add_argument("--output", type=Path, default=Path("data/eval/curation_triage_latest.json"))
	parser.add_argument("--history", type=Path, default=Path("data/eval/curation_triage_history.jsonl"))
	return parser.parse_args()


def _render_select(name: str, selected: str) -> str:
	options = []
	for value in ["deferred", "accepted", "rejected"]:
		is_selected = " selected" if value == selected else ""
		options.append(f'<option value="{value}"{is_selected}>{value}</option>')
	return f'<select name="{html.escape(name)}">{"".join(options)}</select>'


def _render_html(topic: str, model: dict[str, Any] | None, error: str | None) -> str:
	safe_topic = html.escape(topic)
	result_block = ""
	if error:
		result_block = (
			'<section class="card error"><h2>Execution Error</h2>'
			f"<pre>{html.escape(error)}</pre></section>"
		)

	if model:
		curation = model.get("curation", {})
		triage = model.get("triage")
		summary_json = html.escape(json.dumps(curation.get("summary", {}), ensure_ascii=True, indent=2))
		guardrail_json = ""
		if triage is not None:
			guardrail_json = html.escape(json.dumps(triage.get("summary", {}), ensure_ascii=True, indent=2))

		times = curation.get("stage_times_ms", {})
		stage_lines = []
		for stage_name, duration in times.items():
			stage_lines.append(f"{stage_name}: {_format_duration_ms(float(duration))} ({duration} ms)")
		stage_metrics = html.escape("\n".join(stage_lines))

		rows_html: list[str] = []
		for item in model.get("items", []):
			proposal = item.get("proposal", {})
			proposal_id = str(item.get("proposal_id", ""))
			selected = str(item.get("disposition", "deferred"))
			notes = str(item.get("notes", ""))
			reviewer = str(item.get("reviewer", ""))
			approved = bool(item.get("approved", False))
			evidence = html.escape(json.dumps(proposal.get("evidence", []), ensure_ascii=True, indent=2))
			actions = proposal.get("actions", [])
			actions_html = "".join(f"<li>{html.escape(str(action))}</li>" for action in actions)
			approved_checked = " checked" if approved else ""
			rows_html.append(
				"<section class=\"proposal\">"
				f"<h3>{html.escape(proposal_id)} | {html.escape(str(proposal.get('proposal_type', 'unknown')))}</h3>"
				f"<p><strong>{html.escape(str(proposal.get('title', '')))}</strong></p>"
				f"<p>{html.escape(str(proposal.get('rationale', '')))}</p>"
				"<p><strong>Actions</strong></p>"
				f"<ul>{actions_html}</ul>"
				"<details><summary>Evidence</summary>"
				f"<pre>{evidence}</pre></details>"
				"<div class=\"decision-grid\">"
				"<label>Disposition"
				f"{_render_select(f'disposition__{proposal_id}', selected)}"
				"</label>"
				"<label>Decision Notes"
				f"<textarea name=\"notes__{html.escape(proposal_id)}\" rows=\"2\">{html.escape(notes)}</textarea>"
				"</label>"
				"<label>Reviewer (required for accepted)"
				f"<input type=\"text\" name=\"reviewer__{html.escape(proposal_id)}\" value=\"{html.escape(reviewer)}\">"
				"</label>"
				"<label class=\"checkbox\">"
				f"<input type=\"checkbox\" name=\"approved__{html.escape(proposal_id)}\" value=\"true\"{approved_checked}>"
				"Approved"
				"</label>"
				"</div>"
				"</section>"
			)

		items_html = "".join(rows_html) if rows_html else "<p>No proposals generated for this topic.</p>"
		apply_form = ""
		if model.get("items"):
			apply_form = (
				'<section class="card">'
				"<h2>Apply Triage Decisions</h2>"
				'<form method="post">'
				'<input type="hidden" name="action" value="triage">'
				f'<input type="hidden" name="topic" value="{safe_topic}">'
				f'<input type="hidden" name="proposal_generated_at_utc" value="{html.escape(str(model.get("proposal_generated_at_utc", "")))}">'
				f'<input type="hidden" name="default_disposition" value="{html.escape(str(model.get("default_disposition", "deferred")))}">'
				f"{items_html}"
				'<button type="submit">Apply Decisions And Save</button>'
				"</form>"
				"</section>"
			)

		result_block = (
			'<section class="card"><h2>Curation Summary</h2>'
			f"<pre>{summary_json}</pre>"
			"</section>"
			'<section class="grid">'
			'<div class="card"><h3>Stage Times</h3>'
			f"<pre>{stage_metrics}</pre></div>"
			"</section>"
			f"{apply_form}"
		)
		if triage is not None:
			saved_output = html.escape(str(triage.get("output_path", "")))
			result_block += (
				'<section class="card">'
				"<h2>Triage Summary</h2>"
				f"<pre>{guardrail_json}</pre>"
				f"<p><strong>Saved:</strong> {saved_output}</p>"
				"</section>"
			)

	return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Work Knowledge Agent Curator Review</title>
  <style>
    :root {{
      --bg: #eef4f1;
      --card: #ffffff;
      --text: #17221d;
      --muted: #53645c;
      --accent: #146c4f;
      --border: #d4e1da;
      --error: #b42318;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: radial-gradient(circle at top right, #f5faf7 0%, var(--bg) 50%, #e7f0eb 100%);
      color: var(--text);
    }}
    .shell {{ max-width: 1120px; margin: 0 auto; padding: 24px; }}
    .title {{ margin: 0 0 8px; font-size: 1.7rem; }}
    .subtitle {{ margin: 0 0 18px; color: var(--muted); }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px;
      margin-bottom: 14px;
      box-shadow: 0 2px 10px rgba(16, 24, 20, 0.05);
    }}
    .proposal {{
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 12px;
      margin-bottom: 12px;
      background: #fbfdfc;
    }}
    .decision-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; }}
    .checkbox {{ display: flex; align-items: center; gap: 8px; margin-top: 20px; }}
    .error {{ border-color: #f3c4be; color: var(--error); }}
    textarea {{
      width: 100%;
      min-height: 90px;
      padding: 10px;
      border-radius: 10px;
      border: 1px solid var(--border);
      font-size: 0.98rem;
      resize: vertical;
      background: #fcfdfc;
    }}
    input[type=\"text\"], select {{
      width: 100%;
      padding: 8px;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: #ffffff;
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
      background: #f7fbf9;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px;
      font-size: 0.9rem;
      line-height: 1.45;
    }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 12px; }}
  </style>
</head>
<body>
  <main class=\"shell\">
    <h1 class=\"title\">Work Knowledge Agent: Curator Review Console</h1>
    <p class=\"subtitle\">Generate proposals, triage each item, and enforce human approval for accepted decisions.</p>
    <section class=\"card\">
      <form method=\"post\">
        <input type=\"hidden\" name=\"action\" value=\"generate\">
        <label for=\"topic\">Topic</label>
        <textarea id=\"topic\" name=\"topic\" placeholder=\"Enter a curation topic...\">{safe_topic}</textarea>
        <button type=\"submit\">Generate Proposals</button>
      </form>
    </section>
    {result_block}
  </main>
</body>
</html>
"""


class CurationWebHandler(BaseHTTPRequestHandler):
	chunks_path: Path
	metadata_path: Path
	keyword_index_path: Path
	vector_index_path: Path
	config: CurationWorkflowConfig
	default_disposition: str
	output_path: Path
	history_path: Path

	def _send_page(self, topic: str = "", model: dict[str, Any] | None = None, error: str | None = None) -> None:
		content = _render_html(topic=topic, model=model, error=error).encode("utf-8")
		self.send_response(200)
		self.send_header("Content-Type", "text/html; charset=utf-8")
		self.send_header("Content-Length", str(len(content)))
		self.end_headers()
		self.wfile.write(content)

	def _append_history_snapshot(self, payload: dict[str, Any]) -> None:
		event = {
			"event_type": "triage_snapshot",
			"event_timestamp_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
			"channel": "web",
			"output_path": str(self.output_path),
			"topic": ((payload.get("summary") or {}).get("topic", "") if isinstance(payload, dict) else ""),
			"triage_summary": ((payload.get("triage") or {}).get("summary", {}) if isinstance(payload, dict) else {}),
			"payload": payload,
		}
		self.history_path.parent.mkdir(parents=True, exist_ok=True)
		with self.history_path.open("a", encoding="utf-8") as handle:
			handle.write(json.dumps(event, ensure_ascii=True) + "\n")

	def do_GET(self) -> None:  # noqa: N802
		self._send_page()

	def do_POST(self) -> None:  # noqa: N802
		content_length = int(self.headers.get("Content-Length", "0"))
		body = self.rfile.read(content_length).decode("utf-8", errors="replace")
		data = parse_qs(body)
		action = data.get("action", ["generate"])[0].strip().lower()
		topic = data.get("topic", [""])[0].strip()
		if not topic:
			self._send_page(topic=topic, error="Please enter a topic before submitting.")
			return

		try:
			curation_result = run_curation_workflow(
				topic=topic,
				chunks_path=self.chunks_path,
				metadata_path=self.metadata_path,
				keyword_index_path=self.keyword_index_path,
				vector_index_path=self.vector_index_path,
				config=self.config,
			)
			items = []
			for idx, proposal in enumerate(curation_result.proposals, start=1):
				proposal_id = f"proposal-{idx:03d}"
				items.append(
					{
						"proposal_id": proposal_id,
						"proposal": proposal.to_dict(),
						"disposition": self.default_disposition,
						"notes": "",
						"reviewer": "",
						"approved": False,
					}
				)

			model: dict[str, Any] = {
				"default_disposition": self.default_disposition,
				"proposal_generated_at_utc": data.get("proposal_generated_at_utc", [""])[0].strip(),
				"curation": {
					"summary": curation_result.summary,
					"stage_times_ms": curation_result.stage_times_ms,
				},
				"items": items,
			}
			if not model["proposal_generated_at_utc"]:
				# Track when proposals were generated so triage latency can be measured.
				model["proposal_generated_at_utc"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

			if action == "triage":
				decision_timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
				decision_rows: list[dict[str, Any]] = []
				for item in items:
					proposal_id = item["proposal_id"]
					disposition = data.get(f"disposition__{proposal_id}", [self.default_disposition])[0].strip().lower()
					if disposition not in ALLOWED_TRIAGE_DISPOSITIONS:
						disposition = self.default_disposition
					notes = data.get(f"notes__{proposal_id}", [""])[0].strip()
					reviewer = data.get(f"reviewer__{proposal_id}", [""])[0].strip()
					approved = data.get(f"approved__{proposal_id}", [""])[0].strip().lower() == "true"
					decision: dict[str, Any] = {
						"proposal_id": proposal_id,
						"disposition": disposition,
						"notes": notes,
						"decision_timestamp_utc": decision_timestamp,
					}
					if reviewer or approved:
						decision["human_approval"] = {
							"reviewer": reviewer,
							"approved": approved,
							"notes": notes,
						}
					decision_rows.append(decision)
					item["disposition"] = disposition
					item["notes"] = notes
					item["reviewer"] = reviewer
					item["approved"] = approved

				triage_result = run_curation_triage_workflow(
					topic=topic,
					proposals=curation_result.proposals,
					decision_rows=decision_rows,
					default_disposition=self.default_disposition,
					proposal_generated_at_utc=str(model.get("proposal_generated_at_utc", "")).strip() or None,
					decision_channel="web",
				)
				payload = {
					"summary": {
						"topic": topic,
						"curation": curation_result.summary,
						"triage": triage_result.summary,
					},
					"stage_times_ms": curation_result.stage_times_ms,
					"retrieval_hit_count": len(curation_result.retrieval_hits),
					"triage": triage_result.to_dict(),
				}
				self.output_path.parent.mkdir(parents=True, exist_ok=True)
				self.output_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
				self._append_history_snapshot(payload)
				model["triage"] = {
					"summary": triage_result.summary,
					"output_path": str(self.output_path),
				}

			self._send_page(topic=topic, model=model)
		except Exception as exc:  # noqa: BLE001
			self._send_page(topic=topic, error=f"{type(exc).__name__}: {exc}")

	def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
		return


def main() -> None:
	args = parse_args()
	handler_cls = CurationWebHandler
	handler_cls.chunks_path = args.chunks
	handler_cls.metadata_path = args.metadata
	handler_cls.keyword_index_path = args.keyword_index
	handler_cls.vector_index_path = args.vector_index
	handler_cls.default_disposition = args.default_disposition
	handler_cls.output_path = args.output
	handler_cls.history_path = args.history
	handler_cls.config = CurationWorkflowConfig(
		top_k=args.top_k,
		min_metadata_confidence=args.min_metadata_confidence,
		duplicate_similarity_threshold=args.duplicate_similarity_threshold,
		outdated_year_cutoff=args.outdated_year_cutoff,
		allowed_confidentiality=tuple(args.allowed_confidentiality),
		min_query_token_coverage=args.min_query_token_coverage,
	)

	server = ThreadingHTTPServer((args.host, args.port), handler_cls)
	print(f"Curator web console running at http://{args.host}:{args.port}")
	print("Press Ctrl+C to stop.")
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		pass
	finally:
		server.server_close()


if __name__ == "__main__":
	main()
