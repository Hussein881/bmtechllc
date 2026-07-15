# Guardrails and Data Policy Baseline

This document defines the minimum safety and governance policy for the Work
Knowledge Agent. These rules are mandatory for default execution paths.

## 1. Data Classification
- public: shareable outside the team.
- internal: default for normal engineering artifacts.
- confidential: restricted; output must be minimized and redacted.

If classification is missing, treat data as `internal`.

## 2. Source Handling Rules
- Do not commit real confidential documents to git.
- Use synthetic or redacted samples for demos and tests.
- Keep raw source references for traceability, but do not expose sensitive raw
	text in final responses when classification requires protection.

## 3. Response Safety Rules
- No final answer without at least one citation for factual claims.
- Any step not grounded in retrieved sources must be labeled unsupported.
- If evidence is insufficient, return explicit unknowns instead of guessing.

## 4. Confidentiality Enforcement
- Apply redaction before synthesis when content is confidential.
- Block export/write-back for confidential content without human approval.
- Record the reason and timestamp for blocked actions in logs.

## 5. Human Approval Requirement
Human approval is required for:
- proposing changes to knowledge-base source documents,
- publishing curated updates,
- disclosing confidential source excerpts.

## 6. Logging and Auditability
Each workflow request should log:
- request_id,
- component,
- source identifiers used,
- guardrail checks performed,
- allow/deny decision and reason.

## 7. Baseline Incident Process
If a confidentiality or citation policy is violated:
1. Stop release path immediately.
2. Capture impacted workflow inputs and outputs.
3. Patch guardrail logic and add regression tests.
4. Re-run the relevant phase gate before continuing.

