"""Tool: run_llm_eval

Tag: reusable-asset

What this tool does:
- Executes a fixed evaluation set against the configured Phase 3 Watsonx-backed generation path.
- Reports success rate, expected-output match rate, token usage, and latency metrics.

Inputs:
- Eval cases JSON.
- Optional Watsonx project/url/apikey/model overrides.

Outputs:
- Console summary metrics for gate review.
- JSON report file for trend tracking.

Status:
- Phase 3 provider-path evaluation harness.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from work_knowledge_agent.evaluation import evaluate_llm_cases, load_llm_eval_cases
from work_knowledge_agent.models import build_default_llm_client


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 3 LLM evaluation suite.")
    parser.add_argument("--eval-cases", type=Path, default=Path("data/eval/llm_eval_cases.json"))
    parser.add_argument("--report-out", type=Path, default=Path("data/eval/llm_report_latest.json"))
    parser.add_argument("--project-id", default="", help="Override DEBUG_AGENT_LLM_WATSONX_PROJECT_ID")
    parser.add_argument("--url", default="", help="Override DEBUG_AGENT_LLM_WATSONX_URL")
    parser.add_argument("--apikey-file", default="", help="Override DEBUG_AGENT_LLM_WATSONX_APIKEY_FILE")
    parser.add_argument("--iam-token-url", default="", help="Override DEBUG_AGENT_LLM_IAM_TOKEN_URL")
    parser.add_argument("--model-id", default="", help="Override WKA_WATSONX_MODEL_ID")
    parser.add_argument("--api-version", default="", help="Override WKA_WATSONX_API_VERSION")
    parser.add_argument("--prompt-version", default="", help="Override WKA_WATSONX_PROMPT_VERSION")
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

    cases = load_llm_eval_cases(args.eval_cases)
    try:
        client = build_default_llm_client()
        report = evaluate_llm_cases(cases, client)
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(
            "LLM evaluation failed before execution. Ensure Watsonx configuration is available "
            "in the shell or passed as CLI overrides. "
            f"Details: {exc}"
        ) from exc

    args.report_out.parent.mkdir(parents=True, exist_ok=True)
    args.report_out.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")

    metrics = report["metrics"]
    print("LLM eval complete")
    print(f"total_cases={report['total_cases']}")
    print(f"boundary_allow_rate_pct={metrics['boundary_allow_rate_pct']}")
    print(f"generation_success_rate_pct={metrics['generation_success_rate_pct']}")
    print(f"expected_match_rate_pct={metrics['expected_match_rate_pct']}")
    print(f"latency_p50_ms={metrics['latency_p50_ms']}")
    print(f"latency_p95_ms={metrics['latency_p95_ms']}")
    print(f"avg_input_tokens={metrics['avg_input_tokens']}")
    print(f"avg_output_tokens={metrics['avg_output_tokens']}")
    print(f"report_path={args.report_out}")


if __name__ == "__main__":
    main()