"""Unit tests for human-approval guardrail bypass prevention."""

from __future__ import annotations

import unittest

from work_knowledge_agent.guardrails.human_approval import (
	HumanApprovalRecord,
	TriageDecision,
	validate_triage_decision,
)


class HumanApprovalGuardrailTests(unittest.TestCase):
	def test_invalid_disposition_is_rejected(self) -> None:
		with self.assertRaises(ValueError):
			validate_triage_decision(TriageDecision(proposal_id="proposal-001", disposition="ship-it"))

	def test_accepted_requires_approval_true(self) -> None:
		with self.assertRaises(PermissionError):
			validate_triage_decision(
				TriageDecision(
					proposal_id="proposal-001",
					disposition="accepted",
					human_approval=HumanApprovalRecord(reviewer="anwarh", approved=False),
				)
			)

	def test_accepted_requires_non_empty_reviewer(self) -> None:
		with self.assertRaises(PermissionError):
			validate_triage_decision(
				TriageDecision(
					proposal_id="proposal-001",
					disposition="accepted",
					human_approval=HumanApprovalRecord(reviewer="", approved=True),
				)
			)


if __name__ == "__main__":
	unittest.main()
