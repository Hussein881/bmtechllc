"""Security checkpoint for content crossing the LLM boundary."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from work_knowledge_agent.security.redaction import contains_sensitive_data, redact_text


@dataclass(frozen=True)
class LLMBoundaryRequest:
	prompt: str
	context: str
	provider_mode: str = "local"
	confidentiality_level: str = "internal"
	extra_metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class LLMBoundaryCheckResult:
	allowed: bool
	reason: str
	sanitized_prompt: str
	sanitized_context: str
	details: Mapping[str, str] = field(default_factory=dict)


def enforce_llm_boundary(request: LLMBoundaryRequest) -> LLMBoundaryCheckResult:
	provider_mode = request.provider_mode.strip().lower() or "local"
	confidentiality_level = request.confidentiality_level.strip().lower() or "internal"

	if provider_mode not in {"local", "api", "approved_api"}:
		return LLMBoundaryCheckResult(
			allowed=False,
			reason="invalid_provider_mode",
			sanitized_prompt="",
			sanitized_context="",
			details={"provider_mode": provider_mode},
		)

	if provider_mode == "api" and confidentiality_level != "public":
		return LLMBoundaryCheckResult(
			allowed=False,
			reason="api_confidentiality_blocked",
			sanitized_prompt="",
			sanitized_context="",
			details={
				"provider_mode": provider_mode,
				"confidentiality_level": confidentiality_level,
			},
		)

	if provider_mode == "approved_api" and confidentiality_level not in {"public", "internal", "confidential"}:
		return LLMBoundaryCheckResult(
			allowed=False,
			reason="unsupported_confidentiality_level",
			sanitized_prompt="",
			sanitized_context="",
			details={
				"provider_mode": provider_mode,
				"confidentiality_level": confidentiality_level,
			},
		)

	sanitized_prompt = redact_text(request.prompt)
	sanitized_context = redact_text(request.context)
	had_sensitive_data = contains_sensitive_data(request.prompt) or contains_sensitive_data(request.context)

	return LLMBoundaryCheckResult(
		allowed=True,
		reason="ok_redacted" if had_sensitive_data else "ok",
		sanitized_prompt=sanitized_prompt,
		sanitized_context=sanitized_context,
		details={
			"provider_mode": provider_mode,
			"confidentiality_level": confidentiality_level,
			"had_sensitive_data": str(had_sensitive_data).lower(),
		},
	)