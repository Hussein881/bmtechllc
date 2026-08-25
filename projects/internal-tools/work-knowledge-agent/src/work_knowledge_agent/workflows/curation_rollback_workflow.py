"""Rollback helpers for Phase 5 curator triage decisions."""

from __future__ import annotations

from datetime import datetime, timezone
from statistics import median
from typing import Any


def apply_rollback_to_payload(
	payload: dict[str, Any],
	target_decision_id: str,
	reviewer: str,
	reason: str,
	rollback_timestamp_utc: str | None = None,
) -> tuple[dict[str, Any], bool]:
	decision_id = str(target_decision_id or "").strip()
	if not decision_id:
		raise ValueError("target_decision_id is required")
	reviewer_value = str(reviewer or "").strip()
	if not reviewer_value:
		raise ValueError("reviewer is required for rollback")

	rolled_back = False
	timestamp = _resolve_timestamp(rollback_timestamp_utc)
	triage = payload.get("triage", {})
	items = triage.get("items", [])
	if not isinstance(items, list):
		items = []

	for item in items:
		if not isinstance(item, dict):
			continue
		audit = item.get("audit", {})
		if not isinstance(audit, dict):
			audit = {}
		item_decision_id = str(audit.get("decision_id", "")).strip()
		if item_decision_id != decision_id:
			continue
		decision = item.get("decision", {})
		if not isinstance(decision, dict):
			decision = {}
		decision["disposition"] = "deferred"
		decision["notes"] = (
			f"Rolled back by {reviewer_value} at {timestamp}. Reason: {str(reason or '').strip() or 'not provided'}"
		)
		decision.pop("human_approval", None)
		decision["requires_human_approval"] = False
		item["decision"] = decision
		item["rollback"] = {
			"rolled_back": True,
			"rolled_back_at_utc": timestamp,
			"rolled_back_by": reviewer_value,
			"reason": str(reason or "").strip(),
			"target_decision_id": decision_id,
		}
		rolled_back = True
		break

	if not rolled_back:
		return payload, False

	summary = _recompute_summary(items=items, decision_channel=str((triage.get("summary") or {}).get("decision_channel", "unknown")))
	triage["summary"] = summary
	payload["triage"] = triage
	if isinstance(payload.get("summary"), dict):
		payload["summary"]["triage"] = summary
	payload["rollback_summary"] = {
		"target_decision_id": decision_id,
		"rolled_back": True,
		"rolled_back_at_utc": timestamp,
		"rolled_back_by": reviewer_value,
		"reason": str(reason or "").strip(),
	}
	return payload, True


def _recompute_summary(items: list[dict[str, Any]], decision_channel: str) -> dict[str, Any]:
	accepted = 0
	deferred = 0
	rejected = 0
	approved_accepted = 0
	latencies: list[float] = []
	for item in items:
		decision = item.get("decision", {}) if isinstance(item, dict) else {}
		disposition = str((decision or {}).get("disposition", "")).strip().lower()
		if disposition == "accepted":
			accepted += 1
			approval = (decision or {}).get("human_approval", {})
			if isinstance(approval, dict) and bool(approval.get("approved", False)):
				approved_accepted += 1
		elif disposition == "rejected":
			rejected += 1
		else:
			deferred += 1
		latency = item.get("decision_latency_ms", 0.0) if isinstance(item, dict) else 0.0
		try:
			latencies.append(max(0.0, float(latency)))
		except (TypeError, ValueError):
			latencies.append(0.0)

	proposal_count = len(items)
	return {
		"proposal_count": proposal_count,
		"accepted_count": accepted,
		"deferred_count": deferred,
		"rejected_count": rejected,
		"accepted_with_human_approval_count": approved_accepted,
		"approval_ratio_pct": round((accepted / proposal_count * 100.0) if proposal_count else 0.0, 3),
		"decision_latency_ms_p50": round(float(median(latencies)) if latencies else 0.0, 3),
		"decision_latency_ms_p95": round(_p95(latencies), 3),
		"decision_channel": str(decision_channel or "unknown").strip().lower() or "unknown",
	}


def _resolve_timestamp(value: str | None) -> str:
	raw = str(value or "").strip()
	if raw:
		if raw.endswith("Z"):
			raw = raw[:-1] + "+00:00"
		try:
			parsed = datetime.fromisoformat(raw)
		except ValueError as exc:
			raise ValueError(f"Invalid rollback timestamp: {value!r}") from exc
		if parsed.tzinfo is None:
			parsed = parsed.replace(tzinfo=timezone.utc)
		return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat()
	return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _p95(values: list[float]) -> float:
	if not values:
		return 0.0
	sorted_vals = sorted(values)
	idx = min(len(sorted_vals) - 1, int(round(0.95 * (len(sorted_vals) - 1))))
	return float(sorted_vals[idx])
