"""Unit tests for Phase 5 curation triage workflow and approval checkpoints."""

from __future__ import annotations

import unittest

from work_knowledge_agent.agents.curator_agent import CurationProposal
from work_knowledge_agent.workflows.curation_triage_workflow import run_curation_triage_workflow


class CurationTriageWorkflowTests(unittest.TestCase):
	def _proposal(self) -> CurationProposal:
		return CurationProposal(
			proposal_type="missing_knowledge",
			title="Missing runbook for cluster failover",
			rationale="No grounded runbook was found for cluster failover operations.",
			actions=["Add runbook", "Tag source"],
			evidence=[],
			confidence=0.9,
		)

	def test_accepted_requires_human_approval(self) -> None:
		with self.assertRaises(PermissionError):
			run_curation_triage_workflow(
				topic="cluster failover",
				proposals=[self._proposal()],
				decision_rows=[{"proposal_id": "proposal-001", "disposition": "accepted"}],
			)

	def test_accepted_with_human_approval_is_recorded(self) -> None:
		result = run_curation_triage_workflow(
			topic="cluster failover",
			proposals=[self._proposal()],
			proposal_generated_at_utc="2026-07-05T00:00:00+00:00",
			decision_channel="cli",
			decision_rows=[
				{
					"proposal_id": "proposal-001",
					"disposition": "accepted",
					"decision_timestamp_utc": "2026-07-05T00:01:00+00:00",
					"notes": "Ready for write-back planning",
					"human_approval": {
						"reviewer": "anwarh",
						"approved": True,
						"notes": "Approved after evidence review",
					},
				}
			],
		)

		self.assertEqual(result.summary["proposal_count"], 1)
		self.assertEqual(result.summary["accepted_count"], 1)
		self.assertEqual(result.summary["accepted_with_human_approval_count"], 1)
		self.assertEqual(result.summary["approval_ratio_pct"], 100.0)
		self.assertEqual(result.summary["decision_channel"], "cli")
		self.assertGreaterEqual(result.summary["decision_latency_ms_p50"], 60000.0)
		self.assertEqual(len(result.items), 1)
		self.assertEqual(result.items[0]["decision"]["disposition"], "accepted")
		self.assertGreaterEqual(result.items[0]["decision_latency_ms"], 60000.0)
		self.assertEqual(result.items[0]["audit"]["decision_channel"], "cli")
		self.assertEqual(result.items[0]["audit"]["decision_by"], "anwarh")
		self.assertTrue(result.items[0]["audit"]["decision_id"])


if __name__ == "__main__":
	unittest.main()
