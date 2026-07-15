"""Unit tests for Phase 5 curation rollback workflow."""

from __future__ import annotations

import unittest

from work_knowledge_agent.workflows.curation_rollback_workflow import apply_rollback_to_payload


class CurationRollbackWorkflowTests(unittest.TestCase):
	def _payload(self) -> dict:
		return {
			"summary": {"topic": "cluster failover", "triage": {}},
			"triage": {
				"summary": {
					"proposal_count": 1,
					"accepted_count": 1,
					"deferred_count": 0,
					"rejected_count": 0,
					"accepted_with_human_approval_count": 1,
					"approval_ratio_pct": 100.0,
					"decision_latency_ms_p50": 1000.0,
					"decision_latency_ms_p95": 1000.0,
					"decision_channel": "cli",
				},
				"items": [
					{
						"proposal_id": "proposal-001",
						"decision": {
							"proposal_id": "proposal-001",
							"disposition": "accepted",
							"notes": "approved",
							"requires_human_approval": True,
							"human_approval": {
								"reviewer": "anwarh",
								"approved": True,
								"notes": "ok",
								"timestamp_utc": "2026-07-05T00:00:30+00:00",
							},
						},
						"decision_timestamp_utc": "2026-07-05T00:00:30+00:00",
						"decision_latency_ms": 30000.0,
						"audit": {
							"decision_id": "abc123",
							"decision_channel": "cli",
							"decision_by": "anwarh",
						},
					}
				],
			},
		}

	def test_apply_rollback_changes_disposition_and_updates_summary(self) -> None:
		payload, changed = apply_rollback_to_payload(
			payload=self._payload(),
			target_decision_id="abc123",
			reviewer="anwarh",
			reason="incorrect approval",
			rollback_timestamp_utc="2026-07-05T00:02:00+00:00",
		)
		self.assertTrue(changed)
		decision = payload["triage"]["items"][0]["decision"]
		self.assertEqual(decision["disposition"], "deferred")
		self.assertFalse(decision["requires_human_approval"])
		self.assertNotIn("human_approval", decision)
		self.assertEqual(payload["triage"]["summary"]["accepted_count"], 0)
		self.assertEqual(payload["triage"]["summary"]["deferred_count"], 1)
		self.assertEqual(payload["triage"]["summary"]["approval_ratio_pct"], 0.0)
		self.assertTrue(payload["triage"]["items"][0]["rollback"]["rolled_back"])

	def test_apply_rollback_returns_false_when_missing_decision(self) -> None:
		payload, changed = apply_rollback_to_payload(
			payload=self._payload(),
			target_decision_id="missing",
			reviewer="anwarh",
			reason="none",
		)
		self.assertFalse(changed)
		self.assertEqual(payload["triage"]["summary"]["accepted_count"], 1)


if __name__ == "__main__":
	unittest.main()
