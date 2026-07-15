"""Parity checks for CLI vs web triage semantics."""

from __future__ import annotations

import unittest

from work_knowledge_agent.agents.curator_agent import CurationProposal
from work_knowledge_agent.workflows.curation_triage_workflow import run_curation_triage_workflow


class CurationTriageParityTests(unittest.TestCase):
	def _proposal(self) -> CurationProposal:
		return CurationProposal(
			proposal_type="missing_knowledge",
			title="Missing runbook",
			rationale="No grounded runbook found.",
			actions=["Add runbook"],
			evidence=[],
			confidence=0.9,
		)

	def test_cli_and_web_keep_same_disposition_semantics(self) -> None:
		decision_rows = [
			{
				"proposal_id": "proposal-001",
				"disposition": "accepted",
				"decision_timestamp_utc": "2026-07-05T00:01:00+00:00",
				"notes": "approved",
				"human_approval": {
					"reviewer": "anwarh",
					"approved": True,
					"notes": "reviewed",
				},
			}
		]

		cli_result = run_curation_triage_workflow(
			topic="cluster failover",
			proposals=[self._proposal()],
			decision_rows=decision_rows,
			proposal_generated_at_utc="2026-07-05T00:00:00+00:00",
			decision_channel="cli",
		)
		web_result = run_curation_triage_workflow(
			topic="cluster failover",
			proposals=[self._proposal()],
			decision_rows=decision_rows,
			proposal_generated_at_utc="2026-07-05T00:00:00+00:00",
			decision_channel="web",
		)

		self.assertEqual(cli_result.summary["accepted_count"], web_result.summary["accepted_count"])
		self.assertEqual(cli_result.summary["approval_ratio_pct"], web_result.summary["approval_ratio_pct"])
		self.assertEqual(cli_result.items[0]["decision"]["disposition"], web_result.items[0]["decision"]["disposition"])
		self.assertEqual(cli_result.items[0]["decision"]["requires_human_approval"], web_result.items[0]["decision"]["requires_human_approval"])
		self.assertEqual(cli_result.items[0]["audit"]["decision_channel"], "cli")
		self.assertEqual(web_result.items[0]["audit"]["decision_channel"], "web")


if __name__ == "__main__":
	unittest.main()
