"""Optional local API interface for Phase 6 operations."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


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


def _script_path(name: str) -> str:
	project_root = Path(__file__).resolve().parents[3]
	return str(project_root / "scripts" / name)


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
	body = json.dumps(payload, ensure_ascii=True, indent=2).encode("utf-8")
	handler.send_response(status)
	handler.send_header("Content-Type", "application/json")
	handler.send_header("Content-Length", str(len(body)))
	handler.end_headers()
	handler.wfile.write(body)


def create_handler(report_path: Path, markdown_path: Path):
	class Handler(BaseHTTPRequestHandler):
		def log_message(self, format: str, *args: object) -> None:  # noqa: A003
			return

		def do_GET(self) -> None:  # noqa: N802
			if self.path == "/health":
				_json_response(
					self,
					200,
					{
						"status": "ok",
						"service": "work_knowledge_agent_api",
						"time_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
					},
				)
				return

			if self.path == "/phase6/readiness":
				payload = _load_json(report_path)
				if not payload:
					_json_response(
						self,
						404,
						{
							"error": "readiness_report_not_found",
							"report_path": str(report_path),
						},
					)
					return
				_json_response(self, 200, payload)
				return

			if self.path == "/phase6/readiness/packet":
				if not markdown_path.exists():
					_json_response(
						self,
						404,
						{
							"error": "readiness_packet_not_found",
							"packet_path": str(markdown_path),
						},
					)
					return
				_json_response(
					self,
					200,
					{
						"packet_path": str(markdown_path),
						"packet_markdown": markdown_path.read_text(encoding="utf-8"),
					},
				)
				return

			_json_response(self, 404, {"error": "not_found", "path": self.path})

		def do_POST(self) -> None:  # noqa: N802
			if self.path != "/phase6/readiness/run":
				_json_response(self, 404, {"error": "not_found", "path": self.path})
				return

			content_length = int(self.headers.get("Content-Length", "0") or "0")
			raw_body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""
			body: dict[str, Any] = {}
			if raw_body.strip():
				try:
					parsed = json.loads(raw_body)
					if isinstance(parsed, dict):
						body = parsed
				except json.JSONDecodeError:
					_json_response(self, 400, {"error": "invalid_json"})
					return

			run_observability = bool(body.get("run_observability", False))
			command = [
				sys.executable,
				_script_path("run_phase6_readiness.py"),
				"--report-out",
				str(report_path),
				"--markdown-out",
				str(markdown_path),
			]
			if run_observability:
				command.append("--run-observability")

			completed = subprocess.run(command, capture_output=True, text=True, check=False)
			response = {
				"exit_code": int(completed.returncode),
				"stdout": completed.stdout,
				"stderr": completed.stderr,
				"report_path": str(report_path),
				"packet_path": str(markdown_path),
				"run_observability": run_observability,
			}
			if completed.returncode != 0:
				_json_response(self, 500, response)
				return

			response["readiness"] = _load_json(report_path)
			_json_response(self, 200, response)

	return Handler


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Run optional Work Knowledge Agent local API")
	parser.add_argument("--host", default="127.0.0.1")
	parser.add_argument("--port", type=int, default=8770)
	parser.add_argument("--report-path", type=Path, default=Path("data/eval/phase6_readiness_latest.json"))
	parser.add_argument("--markdown-path", type=Path, default=Path("data/eval/phase6_readiness_packet.md"))
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	handler = create_handler(report_path=args.report_path, markdown_path=args.markdown_path)
	server = ThreadingHTTPServer((args.host, args.port), handler)
	print(f"Work Knowledge Agent API running at http://{args.host}:{args.port}")
	print("Endpoints: GET /health, GET /phase6/readiness, GET /phase6/readiness/packet, POST /phase6/readiness/run")
	print("Press Ctrl+C to stop.")
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		pass
	finally:
		server.server_close()


if __name__ == "__main__":
	main()
