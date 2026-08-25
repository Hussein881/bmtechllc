"""Tool: check_llm

Tag: reusable-asset

What this tool does:
- Performs a real live check against the configured model provider endpoint.
- Runs the request through the LLM-boundary guardrail before generation.
- Prints generated text plus provider/model/provenance metadata for debugging.

Inputs:
- Optional prompt/context overrides.
- Optional provider overrides for Watsonx and Anthropic.

Outputs:
- Human-readable or JSON live-check result for the configured LLM path.

Status:
- Phase 3 live connectivity and generation check.
"""

from __future__ import annotations

import argparse
import json
import os

from work_knowledge_agent.guardrails import LLMBoundaryRequest, enforce_llm_boundary
from work_knowledge_agent.models import GenerationRequest, build_default_llm_client


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a live provider-backed generation check.")
    parser.add_argument(
        "--prompt",
        default="Reply with LIVE_CHECK_OK and one short sentence confirming the model is reachable.",
        help="Prompt to send to the model",
    )
    parser.add_argument("--context", default="", help="Optional additional retrieved context")
    parser.add_argument("--project-id", default="", help="Override DEBUG_AGENT_LLM_WATSONX_PROJECT_ID")
    parser.add_argument("--url", default="", help="Override DEBUG_AGENT_LLM_WATSONX_URL")
    parser.add_argument("--apikey-file", default="", help="Override DEBUG_AGENT_LLM_WATSONX_APIKEY_FILE")
    parser.add_argument("--iam-token-url", default="", help="Override DEBUG_AGENT_LLM_IAM_TOKEN_URL")
    parser.add_argument("--model-id", default="", help="Override WKA_WATSONX_MODEL_ID")
    parser.add_argument("--api-version", default="", help="Override WKA_WATSONX_API_VERSION")
    parser.add_argument("--prompt-version", default="", help="Override WKA_WATSONX_PROMPT_VERSION")
    parser.add_argument("--provider", default="", help="Override WKA_LLM_PROVIDER (watsonx|anthropic)")
    parser.add_argument("--anthropic-model-id", default="", help="Override WKA_ANTHROPIC_MODEL_ID")
    parser.add_argument("--anthropic-apikey-file", default="", help="Override WKA_ANTHROPIC_APIKEY_FILE")
    parser.add_argument("--anthropic-api-version", default="", help="Override WKA_ANTHROPIC_API_VERSION")
    parser.add_argument("--anthropic-prompt-version", default="", help="Override WKA_ANTHROPIC_PROMPT_VERSION")
    parser.add_argument("--anthropic-base-url", default="", help="Override WKA_ANTHROPIC_BASE_URL")
    parser.add_argument("--max-output-tokens", type=int, default=96)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser.parse_args()


def _apply_override(env_key: str, value: str) -> None:
    if value.strip():
        os.environ[env_key] = value.strip()


def main() -> None:
    args = parse_args()
    _apply_override("DEBUG_AGENT_LLM_WATSONX_PROJECT_ID", args.project_id)
    _apply_override("DEBUG_AGENT_LLM_WATSONX_URL", args.url)
    _apply_override("DEBUG_AGENT_LLM_WATSONX_APIKEY_FILE", args.apikey_file)
    _apply_override("DEBUG_AGENT_LLM_IAM_TOKEN_URL", args.iam_token_url)
    _apply_override("WKA_WATSONX_MODEL_ID", args.model_id)
    _apply_override("WKA_WATSONX_API_VERSION", args.api_version)
    _apply_override("WKA_WATSONX_PROMPT_VERSION", args.prompt_version)
    _apply_override("WKA_LLM_PROVIDER", args.provider)
    _apply_override("WKA_ANTHROPIC_MODEL_ID", args.anthropic_model_id)
    _apply_override("WKA_ANTHROPIC_APIKEY_FILE", args.anthropic_apikey_file)
    _apply_override("WKA_ANTHROPIC_API_VERSION", args.anthropic_api_version)
    _apply_override("WKA_ANTHROPIC_PROMPT_VERSION", args.anthropic_prompt_version)
    _apply_override("WKA_ANTHROPIC_BASE_URL", args.anthropic_base_url)

    boundary = enforce_llm_boundary(
        LLMBoundaryRequest(
            prompt=args.prompt,
            context=args.context,
            provider_mode="api",
            confidentiality_level="public",
        )
    )
    if not boundary.allowed:
        raise SystemExit(f"LLM boundary blocked the request: {boundary.reason} details={boundary.details}")

    try:
        client = build_default_llm_client()
        result = client.generate(
            GenerationRequest(
                prompt=boundary.sanitized_prompt,
                context=boundary.sanitized_context,
                metadata={"live_check": True},
                temperature=args.temperature,
                max_output_tokens=args.max_output_tokens,
            )
        )
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(
            "LLM live check failed. Ensure provider credentials are available in the shell "
            "(for Watsonx: DEBUG_AGENT_LLM_WATSONX_* vars, for Anthropic: WKA_ANTHROPIC_API_KEY or WKA_ANTHROPIC_APIKEY_FILE) "
            "and WKA_LLM_PROVIDER is configured. "
            f"in the shell or passed as CLI overrides. Details: {exc}"
        ) from exc

    payload = {
        "text": result.text,
        "metadata": {
            "provider": result.metadata.provider,
            "model_name": result.metadata.model_name,
            "prompt_version": result.metadata.prompt_version,
            "request_id": result.metadata.request_id,
            "input_token_count": result.metadata.input_token_count,
            "output_token_count": result.metadata.output_token_count,
            "latency_ms": result.metadata.latency_ms,
            "extra": dict(result.metadata.extra),
        },
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return

    print("LLM Live Check")
    print(result.text)
    print("")
    print(json.dumps(payload["metadata"], ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()