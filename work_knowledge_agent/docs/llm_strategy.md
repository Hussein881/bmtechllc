# LLM Strategy

Purpose:
- Define where model-based generation is allowed in the system.
- Preserve local-first and enterprise-safe behavior as generative workflows are introduced.
- Standardize model access, provenance, and security controls before Phase 3 begins.

## 1) Boundary by Phase
- Phase 2 (Retrieval + Cited Q&A): remain retrieval-first and LLM-free by default.
- Phase 3 (How-To): first approved LLM boundary for grounded synthesis of procedures from retrieved evidence.
- Phase 4 (Planner): second approved LLM boundary for decomposition of vague goals into ordered plans.
- Phase 5 (Curator): mixed mode; deterministic duplicate detection stays heuristic, while model-assisted reasoning may be used for outdated or missing-prerequisite suggestions.

## 2) Model Access Pattern
- All model calls must go through a single client seam, planned as `src/work_knowledge_agent/models/llm_client.py`.
- No workflow or agent should call a provider SDK directly.
- The client seam must expose:
  - provider name,
  - model name/version,
  - prompt version,
  - token counts when available,
  - latency,
  - failure reason.
- Provider choice is environment-driven via `WKA_LLM_PROVIDER`.
- Current approved API providers in the seam:
  - `watsonx` using `DEBUG_AGENT_LLM_WATSONX_*` credentials.
  - `anthropic` using `WKA_ANTHROPIC_API_KEY`.

## 3) Local-First Rule
- Preferred path: local model runtime.
- Allowed exception: approved API-based model calls when local quality/latency is insufficient and confidentiality controls allow it.
- If an API path is enabled, it must be explicitly configured and documented in runbooks and gate evidence.

## 4) Prompt Versioning and Provenance
- Prompt definitions must be versioned and tracked.
- Generated outputs must carry enough provenance to identify:
  - prompt version,
  - model version,
  - retrieval evidence set,
  - generation timestamp.
- Prompt revisions are contract changes for generated workflows and should trigger regression review.

## 5) Security Checkpoint at the LLM Boundary
- Confidentiality and redaction checks must run before any model call.
- External API calls must be blocked unless the content is permitted for that boundary.
- Deterministic guardrails remain mandatory after generation; an LLM may assist, but it may not replace the final safety gate.

## 6) Guardrail Hierarchy
- Deterministic guardrails are non-bypassable.
- Any future verifier-agent logic is additive only and acts as a second opinion.
- Final release gating must continue to rely on deterministic citation, confidentiality, and unsupported-step checks.

## 7) Evaluation Requirements
- Phase 3 and later must add generation-specific evaluation beyond retrieval metrics.
- Required signals:
  - citation precision,
  - grounded-step precision,
  - refusal accuracy when evidence is weak,
  - latency p50/p95,
  - token/cost telemetry when applicable.

## 8) Pre-Phase 3 Decision Checklist
Before Phase 3 implementation begins, confirm:
- chosen local model runtime or approved API fallback,
- `llm_client` interface contract,
- prompt storage/versioning approach,
- LLM-boundary security guardrail design,
- evaluation rubric for generated procedures.

## Last Updated
2026-07-04
