"""Watsonx credential loading helpers for provider-backed LLM clients."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_WATSONX_URL = "https://us-south.ml.cloud.ibm.com"
DEFAULT_WATSONX_APIKEY_FILE = str(Path.home() / ".config" / "iml-agent" / "apikey.json")
DEFAULT_IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"


class CredentialsError(RuntimeError):
	"""Raised when Watson credentials are missing or invalid."""


@dataclass(frozen=True)
class WatsonCredentials:
	project_id: str
	url: str
	apikey: str
	iam_token_url: str


def _expand(path_str: str) -> Path:
	return Path(path_str).expanduser().resolve()


def load_watson_credentials() -> WatsonCredentials:
	"""Load Watson credentials using the same env keys as the IML agent."""
	project_id = os.getenv("DEBUG_AGENT_LLM_WATSONX_PROJECT_ID", "").strip()
	url = os.getenv("DEBUG_AGENT_LLM_WATSONX_URL", DEFAULT_WATSONX_URL).strip()
	apikey_file = os.getenv("DEBUG_AGENT_LLM_WATSONX_APIKEY_FILE", DEFAULT_WATSONX_APIKEY_FILE).strip()
	iam_token_url = os.getenv("DEBUG_AGENT_LLM_IAM_TOKEN_URL", DEFAULT_IAM_TOKEN_URL).strip()

	if not project_id:
		raise CredentialsError("Missing DEBUG_AGENT_LLM_WATSONX_PROJECT_ID")

	key_path = _expand(apikey_file)
	if not key_path.exists():
		raise CredentialsError(f"Watson API key file not found: {key_path}")

	try:
		payload = json.loads(key_path.read_text(encoding="utf-8"))
	except json.JSONDecodeError as exc:
		raise CredentialsError(f"Invalid JSON in Watson API key file: {key_path}") from exc

	if not isinstance(payload, dict):
		raise CredentialsError("Watson API key payload must be a JSON object")

	apikey = str(payload.get("apikey", "")).strip()
	if not apikey:
		raise CredentialsError("Watson API key file is missing 'apikey'")

	return WatsonCredentials(
		project_id=project_id,
		url=url,
		apikey=apikey,
		iam_token_url=iam_token_url,
	)