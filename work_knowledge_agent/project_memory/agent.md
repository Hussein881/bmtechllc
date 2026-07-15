# Project Memory Agent Rule Addendum

Purpose:
- Capture evaluation behavior expectations in a project-memory-local policy note.

## Strict Evaluation Rule (Failure-Seeking)
- Never tune evaluation inputs, expected outputs, or thresholds to manufacture a passing smoke test.
- Treat evaluations as a diagnostic tool to expose system weaknesses, not as a checkbox to continue phases.
- Prefer stricter defaults that reveal holes:
  - require evidence and section compliance,
  - require expected-source coverage (not partial source matches) for gate-style runs,
  - track task/source coverage percentages, not only boolean pass rates,
  - record failure catalogs and run-error rates.
- Any eval “green” result must be accompanied by a quick review of failure catalog and per-case trial details.
- If metrics improve after eval-case edits, document why the edits improved diagnostic quality (not metric convenience).

## Enforcement Note
- This addendum complements root agent policy files.
- If conflicts occur, `AGENTS.md` remains authoritative.
