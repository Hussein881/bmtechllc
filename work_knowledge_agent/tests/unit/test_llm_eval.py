"""Unit tests for LLM evaluation metrics and reporting."""

from __future__ import annotations

import unittest

from work_knowledge_agent.evaluation.llm_eval import LLMEvalCase, evaluate_llm_cases
from work_knowledge_agent.models.llm_client import GenerationMetadata, GenerationRequest, GenerationResult, LLMClient


class _FakeEvalClient(LLMClient):
    def generate(self, request: GenerationRequest) -> GenerationResult:
        if "ALPHA" in request.prompt:
            text = "LIVE_EVAL_ALPHA ready."
            input_tokens = 12
            output_tokens = 4
            latency = 120.0
        else:
            text = "OK_BETA from IBM."
            input_tokens = 10
            output_tokens = 4
            latency = 180.0
        return GenerationResult(
            text=text,
            metadata=GenerationMetadata(
                provider="watsonx-api",
                model_name="ibm/granite-3-8b-instruct",
                prompt_version="phase3-watsonx-v1",
                request_id="req-123",
                input_token_count=input_tokens,
                output_token_count=output_tokens,
                latency_ms=latency,
                extra={},
            ),
        )


class LLMEvalTests(unittest.TestCase):
    def test_evaluate_llm_cases_reports_metrics(self) -> None:
        cases = [
            LLMEvalCase(id="alpha", prompt="Return ALPHA", expected_contains=("ALPHA",)),
            LLMEvalCase(id="beta", prompt="Return BETA", expected_contains=("OK_BETA", "IBM")),
        ]

        report = evaluate_llm_cases(cases, _FakeEvalClient())

        self.assertEqual(report["total_cases"], 2)
        self.assertEqual(report["metrics"]["generation_success_rate_pct"], 100.0)
        self.assertEqual(report["metrics"]["expected_match_rate_pct"], 100.0)
        self.assertEqual(report["metrics"]["latency_p50_ms"], 150.0)
        self.assertEqual(report["metrics"]["avg_input_tokens"], 11.0)
        self.assertEqual(len(report["per_case"]), 2)


if __name__ == "__main__":
    unittest.main()