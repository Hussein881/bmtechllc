"""Human-approval guardrail contracts for curator triage decisions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

ALLOWED_TRIAGE_DISPOSITIONS = {"accepted", "deferred", "rejected"}


def _utc_now_iso() -> str:
	return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class HumanApprovalRecord:
	reviewer: str
	approved: bool
	notes: str = ""
	timestamp_utc: str = field(default_factory=_utc_now_iso)

	def to_dict(self) -> dict:
		return asdict(self)


@dataclass(frozen=True)
class TriageDecision:
	proposal_id: str
	disposition: str
	notes: str = ""
	human_approval: HumanApprovalRecord | None = None

	def normalized_disposition(self) -> str:
		return str(self.disposition or "").strip().lower()

	def to_dict(self) -> dict:
		payload = {
			"proposal_id": self.proposal_id,
			"disposition": self.normalized_disposition(),
			"notes": self.notes,
			"requires_human_approval": self.normalized_disposition() == "accepted",
		}
		if self.human_approval is not None:
			payload["human_approval"] = self.human_approval.to_dict()
		return payload


def validate_triage_decision(decision: TriageDecision) -> None:
	disposition = decision.normalized_disposition()
	if disposition not in ALLOWED_TRIAGE_DISPOSITIONS:
		raise ValueError(f"Invalid triage disposition: {decision.disposition!r}")
	if disposition != "accepted":
		return

	approval = decision.human_approval
	if approval is None:
		raise PermissionError(
			"Accepted proposals require explicit human approval before any write-back action."
		)
	if not approval.approved:
		raise PermissionError(
			"Accepted proposals require human_approval.approved=true before any write-back action."
		)
	if not str(approval.reviewer or "").strip():
		raise PermissionError(
			"Accepted proposals require a non-empty human_approval.reviewer."
		)
