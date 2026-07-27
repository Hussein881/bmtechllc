"""Curation triage workflow with human-approval checkpoints."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from statistics import median
from typing import Any, Sequence

from work_knowledge_agent.agents.curator_agent import CurationProposal
from work_knowledge_agent.guardrails.human_approval import (
	HumanApprovalRecord,
	TriageDecision,
	validate_triage_decision,
)


@dataclass(frozen=True)
class CurationTriageWorkflowResult:
	topic: str
	generated_at_utc: str
	summary: dict[str, Any]
	items: list[dict[str, Any]]

	def to_dict(self) -> dict[str, Any]:
		return {
			"topic": self.topic,
			"generated_at_utc": self.generated_at_utc,
			"summary": self.summary,
			"items": self.items,
		}


def run_curation_triage_workflow(
	topic: str,
	proposals: Sequence[CurationProposal],
	decision_rows: Sequence[dict[str, Any]] | None = None,
	default_disposition: str = "deferred",
	proposal_generated_at_utc: str | None = None,
	decision_channel: str = "unknown",
) -> CurationTriageWorkflowResult:
	rows = list(decision_rows or [])
	decision_by_id = _decision_map(rows)
	items: list[dict[str, Any]] = []
	counts = {"accepted": 0, "deferred": 0, "rejected": 0}
	approval_checked = 0
	generated_dt = _parse_utc_iso(proposal_generated_at_utc) or datetime.now(timezone.utc)
	decision_latencies_ms: list[float] = []

	for idx, proposal in enumerate(proposals, start=1):
		proposal_id = f"proposal-{idx:03d}"
		decision_payload = decision_by_id.get(proposal_id, {})
		disposition = str(decision_payload.get("disposition", default_disposition)).strip().lower()
		notes = str(decision_payload.get("notes", "")).strip()
		approval_payload = decision_payload.get("human_approval")
		human_approval = _build_human_approval(approval_payload)
		decision_dt = _parse_utc_iso(str(decision_payload.get("decision_timestamp_utc", "")).strip()) or datetime.now(timezone.utc)
		decision = TriageDecision(
			proposal_id=proposal_id,
			disposition=disposition,
			notes=notes,
			human_approval=human_approval,
		)
		validate_triage_decision(decision)
		decision_latency_ms = max(0.0, (decision_dt - generated_dt).total_seconds() * 1000.0)
		decision_latencies_ms.append(decision_latency_ms)
		if decision.normalized_disposition() == "accepted":
			approval_checked += 1
		counts[decision.normalized_disposition()] = counts.get(decision.normalized_disposition(), 0) + 1
		items.append(
			{
				"proposal_id": proposal_id,
				"proposal": proposal.to_dict(),
				"decision": decision.to_dict(),
				"decision_timestamp_utc": decision_dt.replace(microsecond=0).isoformat(),
				"decision_latency_ms": round(decision_latency_ms, 3),
				"audit": {
					"audit_record_version": "1.0",
					"decision_id": _decision_id(proposal_id=proposal_id, decision_timestamp_utc=decision_dt.replace(microsecond=0).isoformat()),
					"decision_channel": str(decision_channel or "unknown").strip().lower() or "unknown",
					"proposal_generated_at_utc": generated_dt.replace(microsecond=0).isoformat(),
					"decision_timestamp_utc": decision_dt.replace(microsecond=0).isoformat(),
					"decision_by": (
						str((decision.human_approval.reviewer if decision.human_approval else "") or "").strip()
						or "system"
					),
				},
			}
		)

	proposal_count = len(proposals)
	accepted_count = counts.get("accepted", 0)
	summary = {
		"proposal_count": proposal_count,
		"accepted_count": accepted_count,
		"deferred_count": counts.get("deferred", 0),
		"rejected_count": counts.get("rejected", 0),
		"accepted_with_human_approval_count": approval_checked,
		"approval_ratio_pct": round((accepted_count / proposal_count * 100.0) if proposal_count else 0.0, 3),
		"decision_latency_ms_p50": round(float(median(decision_latencies_ms)) if decision_latencies_ms else 0.0, 3),
		"decision_latency_ms_p95": round(_p95(decision_latencies_ms), 3),
		"decision_channel": str(decision_channel or "unknown").strip().lower() or "unknown",
	}

	return CurationTriageWorkflowResult(
		topic=topic,
		generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
		summary=summary,
		items=items,
	)


def _decision_map(rows: Sequence[dict[str, Any]]) -> dict[str, dict[str, Any]]:
	mapped: dict[str, dict[str, Any]] = {}
	for row in rows:
		if not isinstance(row, dict):
			continue
		proposal_id = str(row.get("proposal_id", "")).strip()
		if not proposal_id:
			continue
		mapped[proposal_id] = row
	return mapped


def _build_human_approval(payload: Any) -> HumanApprovalRecord | None:
	if not isinstance(payload, dict):
		return None
	return HumanApprovalRecord(
		reviewer=str(payload.get("reviewer", "")).strip(),
		approved=bool(payload.get("approved", False)),
		notes=str(payload.get("notes", "")).strip(),
		timestamp_utc=str(payload.get("timestamp_utc", "")).strip()
		or datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
	)


def _parse_utc_iso(value: str) -> datetime | None:
	raw = str(value or "").strip()
	if not raw:
		return None
	if raw.endswith("Z"):
		raw = raw[:-1] + "+00:00"
	try:
		parsed = datetime.fromisoformat(raw)
	except ValueError:
		return None
	if parsed.tzinfo is None:
		return parsed.replace(tzinfo=timezone.utc)
	return parsed.astimezone(timezone.utc)


def _p95(values: list[float]) -> float:
	if not values:
		return 0.0
	sorted_vals = sorted(values)
	idx = min(len(sorted_vals) - 1, int(round(0.95 * (len(sorted_vals) - 1))))
	return float(sorted_vals[idx])


def _decision_id(proposal_id: str, decision_timestamp_utc: str) -> str:
	value = f"{proposal_id}|{decision_timestamp_utc}".encode("utf-8")
	return hashlib.sha256(value).hexdigest()[:16]
