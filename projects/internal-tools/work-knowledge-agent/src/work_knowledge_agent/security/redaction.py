"""Redaction helpers for sensitive data handling.

The goal is conservative masking for common secrets and identifiers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Pattern


@dataclass(frozen=True)
class RedactionRule:
	name: str
	pattern: Pattern[str]
	replacement: str


DEFAULT_RULES: tuple[RedactionRule, ...] = (
	RedactionRule(
		name="email",
		pattern=re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
		replacement="[REDACTED_EMAIL]",
	),
	RedactionRule(
		name="ipv4",
		pattern=re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
		replacement="[REDACTED_IP]",
	),
	RedactionRule(
		name="api_key_like",
		pattern=re.compile(r"\b(?:sk|api|key)[_-]?[A-Za-z0-9]{16,}\b", re.IGNORECASE),
		replacement="[REDACTED_KEY]",
	),
	RedactionRule(
		name="bearer_token",
		pattern=re.compile(r"\bBearer\s+[A-Za-z0-9._\-]+", re.IGNORECASE),
		replacement="Bearer [REDACTED_TOKEN]",
	),
)


def redact_text(text: str, extra_rules: Iterable[RedactionRule] | None = None) -> str:
	"""Mask sensitive patterns in text using default and optional extra rules."""
	if not text:
		return text

	redacted = text
	rules = list(DEFAULT_RULES)
	if extra_rules:
		rules.extend(extra_rules)

	for rule in rules:
		redacted = rule.pattern.sub(rule.replacement, redacted)
	return redacted


def contains_sensitive_data(text: str, extra_rules: Iterable[RedactionRule] | None = None) -> bool:
	"""Return True if any sensitive pattern is detected."""
	if not text:
		return False

	rules = list(DEFAULT_RULES)
	if extra_rules:
		rules.extend(extra_rules)

	return any(rule.pattern.search(text) for rule in rules)

