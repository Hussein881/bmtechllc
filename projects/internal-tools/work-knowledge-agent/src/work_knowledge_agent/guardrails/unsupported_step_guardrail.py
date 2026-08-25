"""Unsupported-step guardrail helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UnsupportedCheckResult:
	is_supported: bool
	message: str


def evaluate_support(has_evidence: bool) -> UnsupportedCheckResult:
	if has_evidence:
		return UnsupportedCheckResult(is_supported=True, message="supported")
	return UnsupportedCheckResult(
		is_supported=False,
		message="unsupported: no sufficiently relevant evidence found",
	)
