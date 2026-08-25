"""Unit tests for Watsonx client response parsing without network calls."""

from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import patch

from work_knowledge_agent.models.llm_client import (
    DEFAULT_ANTHROPIC_PROMPT_VERSION,
    DEFAULT_WATSONX_PROMPT_VERSION,
    AnthropicAPIClient,
    GenerationRequest,
    LLMClientRetryableError,
    WatsonxAPIClient,
    build_default_llm_client,
)
from work_knowledge_agent.models.watsonx_credentials import WatsonCredentials


class _FakeWatsonxClient(WatsonxAPIClient):
    def __init__(self) -> None:
        super().__init__(
            credentials=WatsonCredentials(
                project_id="project-123",
                url="https://us-south.ml.cloud.ibm.com",
                apikey="fake-key",
                iam_token_url="https://iam.cloud.ibm.com/identity/token",
            ),
            model_id="ibm/granite-3-8b-instruct",
            prompt_version=DEFAULT_WATSONX_PROMPT_VERSION,
        )

    def _fetch_iam_token(self) -> str:
        return "fake-token"

    def _invoke_generation_api(self, request: GenerationRequest, token: str, request_id: str):
        self.last_request = request
        self.last_token = token
        self.last_request_id = request_id
        return {
            "model_id": "ibm/granite-3-8b-instruct",
            "model_version": "1.2.3",
            "created_at": "2026-07-04T00:00:00Z",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "LIVE_CHECK_OK reachable.",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 4, "total_tokens": 14},
        }


class _RetryingFakeWatsonxClient(_FakeWatsonxClient):
    def __init__(self) -> None:
        super().__init__()
        self.calls = 0
        self._max_retries = 1
        self._backoff_seconds = 0.0

    def _invoke_generation_api(self, request: GenerationRequest, token: str, request_id: str):
        self.calls += 1
        if self.calls == 1:
            raise LLMClientRetryableError("HTTP 429 from Watsonx: throttled", retry_after_seconds=0.0)
        return super()._invoke_generation_api(request, token, request_id)


class _FakeAnthropicClient(AnthropicAPIClient):
    def __init__(self) -> None:
        super().__init__(
            api_key="fake-key",
            model_id="claude-3-5-sonnet-20241022",
            prompt_version=DEFAULT_ANTHROPIC_PROMPT_VERSION,
        )

    def _invoke_messages_api(self, request: GenerationRequest, request_id: str):
        self.last_request = request
        self.last_request_id = request_id
        return {
            "id": "msg_123",
            "model": "claude-3-5-sonnet-20241022",
            "stop_reason": "end_turn",
            "content": [
                {"type": "text", "text": "LIVE_CHECK_OK reachable."}
            ],
            "usage": {"input_tokens": 12, "output_tokens": 5},
        }


class _RetryingFakeAnthropicClient(_FakeAnthropicClient):
    def __init__(self) -> None:
        super().__init__()
        self.calls = 0
        self._max_retries = 1
        self._backoff_seconds = 0.0

    def _invoke_messages_api(self, request: GenerationRequest, request_id: str):
        self.calls += 1
        if self.calls == 1:
            raise LLMClientRetryableError("HTTP 529 from Anthropic: overloaded", retry_after_seconds=0.0)
        return super()._invoke_messages_api(request, request_id)


class WatsonxAPIClientTests(unittest.TestCase):
    def test_generate_returns_text_and_metadata(self) -> None:
        client = _FakeWatsonxClient()

        result = client.generate(
            GenerationRequest(
                prompt="Summarize",
                context="Use only this context.",
                max_output_tokens=32,
            )
        )

        self.assertEqual(result.text, "LIVE_CHECK_OK reachable.")
        self.assertEqual(result.metadata.provider, "watsonx-api")
        self.assertEqual(result.metadata.model_name, "ibm/granite-3-8b-instruct")
        self.assertEqual(result.metadata.prompt_version, DEFAULT_WATSONX_PROMPT_VERSION)
        self.assertEqual(result.metadata.input_token_count, 10)
        self.assertEqual(result.metadata.output_token_count, 4)
        self.assertEqual(result.metadata.extra["model_version"], "1.2.3")
        self.assertIn("Retrieved context:", client._build_chat_messages(client.last_request)[1]["content"])

    def test_generate_retries_retryable_errors(self) -> None:
        client = _RetryingFakeWatsonxClient()

        result = client.generate(GenerationRequest(prompt="Summarize", context="Use only this context."))

        self.assertEqual(result.text, "LIVE_CHECK_OK reachable.")
        self.assertEqual(client.calls, 2)


class AnthropicAPIClientTests(unittest.TestCase):
    def test_generate_returns_text_and_metadata(self) -> None:
        client = _FakeAnthropicClient()

        result = client.generate(
            GenerationRequest(
                prompt="Summarize",
                context="Use only this context.",
                max_output_tokens=32,
            )
        )

        self.assertEqual(result.text, "LIVE_CHECK_OK reachable.")
        self.assertEqual(result.metadata.provider, "anthropic-api")
        self.assertEqual(result.metadata.model_name, "claude-3-5-sonnet-20241022")
        self.assertEqual(result.metadata.prompt_version, DEFAULT_ANTHROPIC_PROMPT_VERSION)
        self.assertEqual(result.metadata.input_token_count, 12)
        self.assertEqual(result.metadata.output_token_count, 5)
        self.assertEqual(result.metadata.extra["stop_reason"], "end_turn")

    def test_generate_retries_retryable_errors(self) -> None:
        client = _RetryingFakeAnthropicClient()

        result = client.generate(GenerationRequest(prompt="Summarize", context="Use only this context."))

        self.assertEqual(result.text, "LIVE_CHECK_OK reachable.")
        self.assertEqual(client.calls, 2)


class LLMProviderSelectionTests(unittest.TestCase):
    def test_build_default_selects_anthropic(self) -> None:
        with patch.dict(os.environ, {"WKA_LLM_PROVIDER": "anthropic", "WKA_ANTHROPIC_API_KEY": "fake-key"}, clear=False):
            client = build_default_llm_client()
        self.assertIsInstance(client, AnthropicAPIClient)

    def test_build_default_selects_anthropic_using_apikey_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            key_file = os.path.join(tmpdir, "anthropic_apikey.json")
            with open(key_file, "w", encoding="utf-8") as handle:
                handle.write('{"apikey": "fake-key-from-file"}')

            with patch.dict(
                os.environ,
                {
                    "WKA_LLM_PROVIDER": "anthropic",
                    "WKA_ANTHROPIC_API_KEY": "",
                    "WKA_ANTHROPIC_APIKEY_FILE": key_file,
                },
                clear=False,
            ):
                client = build_default_llm_client()
            self.assertIsInstance(client, AnthropicAPIClient)


if __name__ == "__main__":
    unittest.main()