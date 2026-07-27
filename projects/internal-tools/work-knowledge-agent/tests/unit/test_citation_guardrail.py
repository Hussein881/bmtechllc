"""Unit tests for citation guardrail grounding and command verification."""

from __future__ import annotations

import unittest

from work_knowledge_agent.guardrails.citation_guardrail import enforce_citation_guardrail


class CitationGuardrailTests(unittest.TestCase):
    def test_passes_with_grounded_answer_and_command_match(self) -> None:
        answer = "Evidence-based answer:\n1. Use this command:\n$ systemctl restart my-service"
        citations = [{"source_file": "doc.md", "chunk_id": "c1"}]
        evidence = {"c1": "Run: $ systemctl restart my-service then verify status."}

        result = enforce_citation_guardrail(answer, citations, evidence_by_chunk=evidence)
        self.assertTrue(result.passed)
        self.assertEqual(result.reason, "ok")

    def test_fails_when_command_missing_from_evidence(self) -> None:
        answer = "Evidence-based answer:\n1. Run this operation now:\n$ kubectl delete pod bad-pod"
        citations = [{"source_file": "doc.md", "chunk_id": "c1"}]
        evidence = {
            "c1": (
                "Run this operation now for local service operations and verify outcome. "
                "Use systemctl restart for local service operations."
            )
        }

        result = enforce_citation_guardrail(answer, citations, evidence_by_chunk=evidence)
        self.assertFalse(result.passed)
        self.assertEqual(result.reason, "command_not_in_evidence")

    def test_grounding_threshold_regression_fails_below_threshold(self) -> None:
        answer = "Restart service using systemctl and then verify status quickly"
        citations = [{"source_file": "doc.md", "chunk_id": "c1"}]
        evidence = {"c1": "Restart service using systemctl"}

        result = enforce_citation_guardrail(
            answer,
            citations,
            evidence_by_chunk=evidence,
            grounding_threshold=0.60,
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.reason, "grounding_below_threshold")

    def test_grounding_threshold_regression_passes_at_tuned_threshold(self) -> None:
        answer = "Restart service using systemctl and then verify status quickly"
        citations = [{"source_file": "doc.md", "chunk_id": "c1"}]
        evidence = {"c1": "Restart service using systemctl"}

        result = enforce_citation_guardrail(
            answer,
            citations,
            evidence_by_chunk=evidence,
            grounding_threshold=0.44,
        )
        self.assertTrue(result.passed)
        self.assertEqual(result.reason, "ok")

    def test_sudo_prefixed_command_matches_evidence_variant(self) -> None:
        answer = "Steps:\n$ sudo ./health-check.sh --target app1"
        citations = [{"source_file": "doc.md", "chunk_id": "c1"}]
        evidence = {"c1": "Use ./health-check.sh --target app1 and review output."}

        result = enforce_citation_guardrail(answer, citations, evidence_by_chunk=evidence)
        self.assertTrue(result.passed)
        self.assertEqual(result.reason, "ok")


if __name__ == "__main__":
    unittest.main()
