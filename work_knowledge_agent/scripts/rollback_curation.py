"""Tool: rollback_curation

Tag: reusable-asset

What this tool does:
- Rolls back a previously accepted curator triage decision.
- Updates the latest triage artifact with deferred disposition and rollback metadata.
- Appends a rollback event to triage history for audit continuity.

Inputs:
- Target decision id.
- Reviewer and rollback reason.
- Triage output artifact and history file paths.

Outputs:
- Updated triage artifact with rollback summary.
- Appended rollback event in history JSONL.

Status:
- Phase 5 rollback control baseline.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from work_knowledge_agent.workflows.curation_rollback_workflow import apply_rollback_to_payload


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Rollback a curator triage decision by decision id.")
	parser.add_argument("--decision-id", required=True, help="Decision id to rollback")
	parser.add_argument("--reviewer", required=True, help="Reviewer performing rollback")
	parser.add_argument("--reason", default="", help="Reason for rollback")
	parser.add_argument("--triage", type=Path, default=Path("data/eval/curation_triage_latest.json"))
	parser.add_argument("--history", type=Path, default=Path("data/eval/curation_triage_history.jsonl"))
	parser.add_argument("--rollback-at", default="", help="Optional rollback timestamp (ISO)")
	parser.add_argument("--json", action="store_true", help="Emit machine-readable output")
	return parser.parse_args()


def _load_json(path: Path) -> dict[str, Any]:
	if not path.exists() or not path.read_text(encoding="utf-8").strip():
		return {}
	payload = json.loads(path.read_text(encoding="utf-8"))
	if isinstance(payload, dict):
		return payload
	return {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def _append_history_event(path: Path, event: dict[str, Any]) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	with path.open("a", encoding="utf-8") as handle:
		handle.write(json.dumps(event, ensure_ascii=True) + "\n")


def main() -> None:
	args = parse_args()
	payload = _load_json(args.triage)
	if not payload:
		raise SystemExit(f"No triage artifact found at {args.triage}")

	updated_payload, rolled_back = apply_rollback_to_payload(
		payload=payload,
		target_decision_id=args.decision_id,
		reviewer=args.reviewer,
		reason=args.reason,
		rollback_timestamp_utc=str(args.rollback_at or "").strip() or None,
	)
	if not rolled_back:
		raise SystemExit(f"Decision id not found: {args.decision_id}")

	_write_json(args.triage, updated_payload)
	rollback_meta = updated_payload.get("rollback_summary", {})
	rollback_event = {
		"event_type": "rollback",
		"event_timestamp_utc": rollback_meta.get("rolled_back_at_utc")
		or datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
		"decision_id": args.decision_id,
		"reviewer": args.reviewer,
		"reason": args.reason,
		"triage_path": str(args.triage),
	}
	_append_history_event(args.history, rollback_event)

	if args.json:
		print(json.dumps(updated_payload, ensure_ascii=True, indent=2))
		return

	print("Rollback complete")
	print(f"decision_id={args.decision_id}")
	print(f"triage_path={args.triage}")
	print(f"history_path={args.history}")


if __name__ == "__main__":
	main()
