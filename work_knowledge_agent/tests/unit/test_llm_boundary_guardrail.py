"""Unit tests for the Phase 3 LLM-boundary guardrail."""

from __future__ import annotations

import unittest

from work_knowledge_agent.guardrails import LLMBoundaryRequest, enforce_llm_boundary


class LLMBoundaryGuardrailTests(unittest.TestCase):
	def test_local_mode_allows_internal_content_with_redaction(self) -> None:
		result = enforce_llm_boundary(
			LLMBoundaryRequest(
				prompt="Summarize server health for admin@example.com",
				context="Contact admin@example.com or use Bearer abcdefghijklmnop",
				provider_mode="local",
				confidentiality_level="internal",
			)
		)

		self.assertTrue(result.allowed)
		self.assertEqual(result.reason, "ok_redacted")
		self.assertIn("[REDACTED_EMAIL]", result.sanitized_prompt)
		self.assertIn("[REDACTED_TOKEN]", result.sanitized_context)

	def test_api_mode_blocks_non_public_content(self) -> None:
		result = enforce_llm_boundary(
			LLMBoundaryRequest(
				prompt="Build a runbook",
				context="Internal instructions",
				provider_mode="api",
				confidentiality_level="internal",
			)
		)

		self.assertFalse(result.allowed)
		self.assertEqual(result.reason, "api_confidentiality_blocked")

	def test_approved_api_mode_allows_internal_content(self) -> None:
		result = enforce_llm_boundary(
			LLMBoundaryRequest(
				prompt="Create a procedure",
				context="Internal runbook steps",
				provider_mode="approved_api",
				confidentiality_level="internal",
			)
		)

		self.assertTrue(result.allowed)
		self.assertEqual(result.reason, "ok")


if __name__ == "__main__":
	unittest.main()