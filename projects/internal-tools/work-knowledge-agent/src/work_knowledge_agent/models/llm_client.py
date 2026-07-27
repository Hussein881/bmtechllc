"""Shared LLM client seam for Phase 3+ generative workflows.

This module defines the only approved interface for model-backed generation.
Phase 2 remains LLM-free by default; Phase 3+ workflows should depend on
this contract rather than on provider-specific SDKs.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from work_knowledge_agent.models.watsonx_credentials import WatsonCredentials, load_watson_credentials


DEFAULT_WATSONX_MODEL_ID = "ibm/granite-3-8b-instruct"
DEFAULT_WATSONX_API_VERSION = "2024-03-14"
DEFAULT_WATSONX_PROMPT_VERSION = "phase3-watsonx-v1"
DEFAULT_ANTHROPIC_MODEL_ID = "claude-3-5-sonnet-20241022"
DEFAULT_ANTHROPIC_API_VERSION = "2023-06-01"
DEFAULT_ANTHROPIC_PROMPT_VERSION = "phase3-anthropic-v1"
DEFAULT_ANTHROPIC_BASE_URL = "https://api.anthropic.com"
DEFAULT_ANTHROPIC_APIKEY_FILE = str(Path.home() / ".config" / "iml-agent" / "anthropic_apikey.json")


class LLMClientError(RuntimeError):
	"""Raised when a model call cannot be completed."""


class LLMClientRetryableError(LLMClientError):
	"""Raised when a model call failed for a retryable reason."""

	def __init__(self, message: str, *, retry_after_seconds: float | None = None) -> None:
		super().__init__(message)
		self.retry_after_seconds = retry_after_seconds


@dataclass(frozen=True)
class GenerationMetadata:
	provider: str
	model_name: str
	prompt_version: str
	request_id: str | None = None
	input_token_count: int | None = None
	output_token_count: int | None = None
	latency_ms: float | None = None
	failure_reason: str | None = None
	extra: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GenerationRequest:
	prompt: str
	context: str
	metadata: Mapping[str, Any] = field(default_factory=dict)
	temperature: float = 0.0
	max_output_tokens: int | None = None
	seed: int | None = None


@dataclass(frozen=True)
class GenerationResult:
	text: str
	metadata: GenerationMetadata


class LLMClient(ABC):
	"""Abstract client seam for all approved model calls."""

	@abstractmethod
	def generate(self, request: GenerationRequest) -> GenerationResult:
		"""Generate grounded text from a prompt and retrieved context."""


class LocalOnlyLLMClient(LLMClient):
	"""Default local-first client placeholder.

	This intentionally does not call a provider yet. It exists so Phase 3 can
	build against a stable contract while provider selection remains gated.
	"""

	def __init__(self, model_name: str = "unconfigured-local-model", prompt_version: str = "phase3-draft") -> None:
		self._model_name = model_name
		self._prompt_version = prompt_version

	def generate(self, request: GenerationRequest) -> GenerationResult:
		start = time.perf_counter()
		latency_ms = (time.perf_counter() - start) * 1000.0
		raise NotImplementedError(
			"LocalOnlyLLMClient is a Phase 3 contract scaffold. "
			"Configure a local runtime or approved API-backed implementation before use. "
			f"model={self._model_name} prompt_version={self._prompt_version} latency_ms={latency_ms:.3f}"
		)


class WatsonxAPIClient(LLMClient):
	"""API-backed Watsonx client implementation for Phase 3+ workflows."""

	def __init__(
		self,
		credentials: WatsonCredentials,
		model_id: str = DEFAULT_WATSONX_MODEL_ID,
		prompt_version: str = DEFAULT_WATSONX_PROMPT_VERSION,
		api_version: str = DEFAULT_WATSONX_API_VERSION,
		timeout_seconds: float = 60.0,
		max_retries: int = 2,
		backoff_seconds: float = 1.0,
	) -> None:
		self._credentials = credentials
		self._model_id = model_id
		self._prompt_version = prompt_version
		self._api_version = api_version
		self._timeout_seconds = timeout_seconds
		self._max_retries = max(0, int(max_retries))
		self._backoff_seconds = max(0.0, float(backoff_seconds))

	@classmethod
	def from_env(
		cls,
		model_id: str | None = None,
		prompt_version: str = DEFAULT_WATSONX_PROMPT_VERSION,
		api_version: str = DEFAULT_WATSONX_API_VERSION,
		timeout_seconds: float = 60.0,
	) -> "WatsonxAPIClient":
		credentials = load_watson_credentials()
		resolved_model_id = model_id or os.getenv("WKA_WATSONX_MODEL_ID", DEFAULT_WATSONX_MODEL_ID).strip()
		resolved_api_version = os.getenv("WKA_WATSONX_API_VERSION", api_version).strip() or DEFAULT_WATSONX_API_VERSION
		resolved_prompt_version = os.getenv("WKA_WATSONX_PROMPT_VERSION", prompt_version).strip() or DEFAULT_WATSONX_PROMPT_VERSION
		return cls(
			credentials=credentials,
			model_id=resolved_model_id,
			prompt_version=resolved_prompt_version,
			api_version=resolved_api_version,
			timeout_seconds=timeout_seconds,
			max_retries=int(os.getenv("WKA_WATSONX_MAX_RETRIES", "2")),
			backoff_seconds=float(os.getenv("WKA_WATSONX_RETRY_BACKOFF_SECONDS", "1.0")),
		)

	def generate(self, request: GenerationRequest) -> GenerationResult:
		request_id = str(request.metadata.get("request_id") or uuid.uuid4())
		start = time.perf_counter()
		token = self._fetch_iam_token()
		attempt = 0
		while True:
			try:
				response = self._invoke_generation_api(request=request, token=token, request_id=request_id)
				latency_ms = (time.perf_counter() - start) * 1000.0
				result = self._parse_generation_response(
					response,
					request_id=request_id,
					latency_ms=latency_ms,
					request_seed=request.seed,
				)
				return result
			except LLMClientRetryableError as exc:
				if attempt >= self._max_retries:
					latency_ms = (time.perf_counter() - start) * 1000.0
					raise LLMClientError(
						f"Watsonx generation failed after retries: {exc} request_id={request_id} latency_ms={latency_ms:.3f}"
					) from exc
				delay = exc.retry_after_seconds if exc.retry_after_seconds is not None else self._backoff_seconds * (2 ** attempt)
				attempt += 1
				time.sleep(delay)
			except Exception as exc:  # noqa: BLE001
				latency_ms = (time.perf_counter() - start) * 1000.0
				raise LLMClientError(
					f"Watsonx generation failed: {exc} request_id={request_id} latency_ms={latency_ms:.3f}"
				) from exc

	def _fetch_iam_token(self) -> str:
		payload = urllib.parse.urlencode(
			{
				"grant_type": "urn:ibm:params:oauth:grant-type:apikey",
				"apikey": self._credentials.apikey,
			}
		).encode("utf-8")
		request = urllib.request.Request(
			self._credentials.iam_token_url,
			data=payload,
			headers={
				"Content-Type": "application/x-www-form-urlencoded",
				"Accept": "application/json",
			},
			method="POST",
		)
		response = self._read_json_response(request)
		access_token = str(response.get("access_token", "")).strip()
		if not access_token:
			raise LLMClientError("Watsonx IAM response did not include access_token")
		return access_token

	def _invoke_generation_api(self, request: GenerationRequest, token: str, request_id: str) -> Mapping[str, Any]:
		endpoint = (
			f"{self._credentials.url.rstrip('/')}/ml/v1/text/chat"
			f"?version={urllib.parse.quote(self._api_version)}"
		)
		payload = {
			"model_id": self._model_id,
			"project_id": self._credentials.project_id,
			"messages": self._build_chat_messages(request),
			"max_tokens": int(request.max_output_tokens or 512),
			"time_limit": int(self._timeout_seconds * 1000),
		}
		if request.seed is not None:
			payload["seed"] = int(request.seed)
		if request.temperature > 0.0:
			payload["temperature"] = request.temperature
		http_request = urllib.request.Request(
			endpoint,
			data=json.dumps(payload).encode("utf-8"),
			headers={
				"Authorization": f"Bearer {token}",
				"Content-Type": "application/json",
				"Accept": "application/json",
				"X-Global-Transaction-Id": request_id,
			},
			method="POST",
		)
		return self._read_json_response(http_request)

	def _read_json_response(self, request: urllib.request.Request) -> Mapping[str, Any]:
		try:
			with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
				payload = response.read().decode("utf-8")
		except urllib.error.HTTPError as exc:
			body = exc.read().decode("utf-8", errors="replace")
			if exc.code in {429, 503}:
				retry_after = _retry_after_seconds(exc.headers.get("Retry-After"))
				raise LLMClientRetryableError(
					f"HTTP {exc.code} from Watsonx: {body}",
					retry_after_seconds=retry_after,
				) from exc
			raise LLMClientError(f"HTTP {exc.code} from Watsonx: {body}") from exc
		except urllib.error.URLError as exc:
			raise LLMClientRetryableError(f"Network error calling Watsonx: {exc.reason}") from exc

		try:
			decoded = json.loads(payload)
		except json.JSONDecodeError as exc:
			raise LLMClientError(f"Watsonx returned non-JSON response: {payload[:500]}") from exc

		if not isinstance(decoded, dict):
			raise LLMClientError("Watsonx response payload must be a JSON object")
		return decoded

	def _build_input_text(self, request: GenerationRequest) -> str:
		prompt = request.prompt.strip()
		context = request.context.strip()
		if context:
			return f"{prompt}\n\nRetrieved context:\n{context}"
		return prompt

	def _build_chat_messages(self, request: GenerationRequest) -> list[dict[str, str]]:
		prompt = request.prompt.strip()
		context = request.context.strip()
		user_content = prompt if not context else f"{prompt}\n\nRetrieved context:\n{context}"
		return [
			{
				"role": "system",
				"content": "You are a grounded engineering assistant. Use only the provided context and do not invent unsupported details.",
			},
			{
				"role": "user",
				"content": user_content,
			},
		]

	def _parse_generation_response(
		self,
		response: Mapping[str, Any],
		request_id: str,
		latency_ms: float,
		request_seed: int | None,
	) -> GenerationResult:
		choices = response.get("choices")
		if not isinstance(choices, list) or not choices:
			raise LLMClientError(f"Watsonx response did not include chat choices: {response}")
		first = choices[0]
		if not isinstance(first, dict):
			raise LLMClientError(f"Watsonx choice item was not an object: {first}")

		text = self._extract_chat_text(first).strip()
		if not text:
			raise LLMClientError(f"Watsonx generated empty text: {response}")

		metadata = GenerationMetadata(
			provider="watsonx-api",
			model_name=str(response.get("model_id") or self._model_id),
			prompt_version=self._prompt_version,
			request_id=request_id,
			input_token_count=_to_int((response.get("usage") or {}).get("prompt_tokens")),
			output_token_count=_to_int((response.get("usage") or {}).get("completion_tokens")),
			latency_ms=round(latency_ms, 3),
			failure_reason=None,
			extra={
				"api_version": self._api_version,
				"model_version": str(response.get("model_version", "")).strip(),
				"finish_reason": str(first.get("finish_reason", "")).strip(),
				"created_at": str(response.get("created_at", "")).strip(),
				"seed": "" if request_seed is None else str(request_seed),
			},
		)
		return GenerationResult(text=text, metadata=metadata)

	def _extract_chat_text(self, first_choice: Mapping[str, Any]) -> str:
		message = first_choice.get("message")
		if not isinstance(message, dict):
			return ""
		content = message.get("content", "")
		if isinstance(content, str):
			return content
		if isinstance(content, list):
			parts: list[str] = []
			for item in content:
				if isinstance(item, dict) and item.get("type") == "text":
					parts.append(str(item.get("text", "")))
			return "".join(parts)
		return str(content)


class AnthropicAPIClient(LLMClient):
	"""API-backed Anthropic Claude client implementation for Phase 3+ workflows."""

	def __init__(
		self,
		api_key: str,
		model_id: str = DEFAULT_ANTHROPIC_MODEL_ID,
		prompt_version: str = DEFAULT_ANTHROPIC_PROMPT_VERSION,
		api_version: str = DEFAULT_ANTHROPIC_API_VERSION,
		base_url: str = DEFAULT_ANTHROPIC_BASE_URL,
		timeout_seconds: float = 60.0,
		max_retries: int = 2,
		backoff_seconds: float = 1.0,
	) -> None:
		resolved_key = (api_key or "").strip()
		if not resolved_key:
			raise LLMClientError("Missing WKA_ANTHROPIC_API_KEY")
		self._api_key = resolved_key
		self._model_id = model_id
		self._prompt_version = prompt_version
		self._api_version = api_version
		self._base_url = base_url.rstrip("/")
		self._timeout_seconds = timeout_seconds
		self._max_retries = max(0, int(max_retries))
		self._backoff_seconds = max(0.0, float(backoff_seconds))

	@classmethod
	def from_env(
		cls,
		model_id: str | None = None,
		prompt_version: str = DEFAULT_ANTHROPIC_PROMPT_VERSION,
		api_version: str = DEFAULT_ANTHROPIC_API_VERSION,
		timeout_seconds: float = 60.0,
	) -> "AnthropicAPIClient":
		api_key = os.getenv("WKA_ANTHROPIC_API_KEY", "").strip()
		if not api_key:
			apikey_file = os.getenv("WKA_ANTHROPIC_APIKEY_FILE", DEFAULT_ANTHROPIC_APIKEY_FILE).strip()
			api_key = _load_apikey_from_json_file(apikey_file, provider_name="Anthropic")
		resolved_model_id = model_id or os.getenv("WKA_ANTHROPIC_MODEL_ID", DEFAULT_ANTHROPIC_MODEL_ID).strip()
		resolved_api_version = os.getenv("WKA_ANTHROPIC_API_VERSION", api_version).strip() or DEFAULT_ANTHROPIC_API_VERSION
		resolved_prompt_version = os.getenv("WKA_ANTHROPIC_PROMPT_VERSION", prompt_version).strip() or DEFAULT_ANTHROPIC_PROMPT_VERSION
		resolved_base_url = os.getenv("WKA_ANTHROPIC_BASE_URL", DEFAULT_ANTHROPIC_BASE_URL).strip() or DEFAULT_ANTHROPIC_BASE_URL
		return cls(
			api_key=api_key,
			model_id=resolved_model_id,
			prompt_version=resolved_prompt_version,
			api_version=resolved_api_version,
			base_url=resolved_base_url,
			timeout_seconds=timeout_seconds,
			max_retries=int(os.getenv("WKA_ANTHROPIC_MAX_RETRIES", "2")),
			backoff_seconds=float(os.getenv("WKA_ANTHROPIC_RETRY_BACKOFF_SECONDS", "1.0")),
		)

	def generate(self, request: GenerationRequest) -> GenerationResult:
		request_id = str(request.metadata.get("request_id") or uuid.uuid4())
		start = time.perf_counter()
		attempt = 0
		while True:
			try:
				response = self._invoke_messages_api(request=request, request_id=request_id)
				latency_ms = (time.perf_counter() - start) * 1000.0
				return self._parse_messages_response(
					response,
					request_id=request_id,
					latency_ms=latency_ms,
					request_seed=request.seed,
				)
			except LLMClientRetryableError as exc:
				if attempt >= self._max_retries:
					latency_ms = (time.perf_counter() - start) * 1000.0
					raise LLMClientError(
						f"Anthropic generation failed after retries: {exc} request_id={request_id} latency_ms={latency_ms:.3f}"
					) from exc
				delay = exc.retry_after_seconds if exc.retry_after_seconds is not None else self._backoff_seconds * (2 ** attempt)
				attempt += 1
				time.sleep(delay)
			except Exception as exc:  # noqa: BLE001
				latency_ms = (time.perf_counter() - start) * 1000.0
				raise LLMClientError(
					f"Anthropic generation failed: {exc} request_id={request_id} latency_ms={latency_ms:.3f}"
				) from exc

	def _invoke_messages_api(self, request: GenerationRequest, request_id: str) -> Mapping[str, Any]:
		endpoint = f"{self._base_url}/v1/messages"
		payload = {
			"model": self._model_id,
			"max_tokens": int(request.max_output_tokens or 512),
			"messages": [
				{
					"role": "user",
					"content": self._build_user_content(request),
				}
			],
			"system": "You are a grounded engineering assistant. Use only the provided context and do not invent unsupported details.",
		}
		if request.temperature > 0.0:
			payload["temperature"] = request.temperature
		http_request = urllib.request.Request(
			endpoint,
			data=json.dumps(payload).encode("utf-8"),
			headers={
				"x-api-key": self._api_key,
				"anthropic-version": self._api_version,
				"content-type": "application/json",
				"accept": "application/json",
				"x-request-id": request_id,
			},
			method="POST",
		)
		return self._read_json_response(http_request)

	def _read_json_response(self, request: urllib.request.Request) -> Mapping[str, Any]:
		try:
			with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
				payload = response.read().decode("utf-8")
		except urllib.error.HTTPError as exc:
			body = exc.read().decode("utf-8", errors="replace")
			if exc.code in {429, 500, 503, 529}:
				retry_after = _retry_after_seconds(exc.headers.get("Retry-After"))
				raise LLMClientRetryableError(
					f"HTTP {exc.code} from Anthropic: {body}",
					retry_after_seconds=retry_after,
				) from exc
			raise LLMClientError(f"HTTP {exc.code} from Anthropic: {body}") from exc
		except urllib.error.URLError as exc:
			raise LLMClientRetryableError(f"Network error calling Anthropic: {exc.reason}") from exc

		try:
			decoded = json.loads(payload)
		except json.JSONDecodeError as exc:
			raise LLMClientError(f"Anthropic returned non-JSON response: {payload[:500]}") from exc

		if not isinstance(decoded, dict):
			raise LLMClientError("Anthropic response payload must be a JSON object")
		return decoded

	def _build_user_content(self, request: GenerationRequest) -> str:
		prompt = request.prompt.strip()
		context = request.context.strip()
		if context:
			return f"{prompt}\n\nRetrieved context:\n{context}"
		return prompt

	def _parse_messages_response(
		self,
		response: Mapping[str, Any],
		request_id: str,
		latency_ms: float,
		request_seed: int | None,
	) -> GenerationResult:
		text = self._extract_messages_text(response).strip()
		if not text:
			raise LLMClientError(f"Anthropic generated empty text: {response}")

		usage = response.get("usage") if isinstance(response.get("usage"), dict) else {}
		metadata = GenerationMetadata(
			provider="anthropic-api",
			model_name=str(response.get("model") or self._model_id),
			prompt_version=self._prompt_version,
			request_id=request_id,
			input_token_count=_to_int(usage.get("input_tokens")),
			output_token_count=_to_int(usage.get("output_tokens")),
			latency_ms=round(latency_ms, 3),
			failure_reason=None,
			extra={
				"api_version": self._api_version,
				"stop_reason": str(response.get("stop_reason", "")).strip(),
				"anthropic_id": str(response.get("id", "")).strip(),
				"seed": "" if request_seed is None else str(request_seed),
			},
		)
		return GenerationResult(text=text, metadata=metadata)

	def _extract_messages_text(self, response: Mapping[str, Any]) -> str:
		content = response.get("content")
		if not isinstance(content, list):
			return ""
		parts: list[str] = []
		for item in content:
			if not isinstance(item, dict):
				continue
			if str(item.get("type", "")).strip() == "text":
				parts.append(str(item.get("text", "")))
		return "".join(parts)


def build_default_llm_client() -> LLMClient:
	"""Build the default approved LLM client.

	Provider selection is environment-driven using WKA_LLM_PROVIDER.
	"""
	provider = os.getenv("WKA_LLM_PROVIDER", "watsonx").strip().lower()
	if provider in {"watsonx", "ibm", "ibm-watsonx"}:
		return WatsonxAPIClient.from_env()
	if provider in {"anthropic", "claude"}:
		return AnthropicAPIClient.from_env()
	raise LLMClientError(
		"Unsupported WKA_LLM_PROVIDER. Expected one of: watsonx, anthropic"
	)


def _to_int(value: Any) -> int | None:
	if value is None:
		return None
	try:
		return int(value)
	except (TypeError, ValueError):
		return None


def _retry_after_seconds(value: str | None) -> float | None:
	if not value:
		return None
	try:
		return float(value)
	except ValueError:
		return None


def _load_apikey_from_json_file(path_str: str, provider_name: str) -> str:
	path = Path(path_str).expanduser().resolve()
	if not path.exists():
		return ""
	try:
		payload = json.loads(path.read_text(encoding="utf-8"))
	except json.JSONDecodeError as exc:
		raise LLMClientError(f"Invalid JSON in {provider_name} API key file: {path}") from exc
	if not isinstance(payload, dict):
		raise LLMClientError(f"{provider_name} API key payload must be a JSON object: {path}")
	apikey = str(payload.get("apikey", "")).strip()
	if not apikey:
		raise LLMClientError(f"{provider_name} API key file is missing 'apikey': {path}")
	return apikey