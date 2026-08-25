# Completeness Assessment — `benchmark-cli-tool`

**Date:** 2026-08-06 (revision 3 — supersedes revisions 1 and 2)
**Scope:** `bmtechllc/projects/internal-tools/benchmark-cli-tool`
**Assessed against:** *Week 1 Deliverables* and *Build baseline document Q&A CLI*
**Reviewed at:** commit `ff3e25e` **plus uncommitted working-tree changes** to `agent.py`,
`eval_suite.py`, `prompts.py`, `report.md`, `eval_results.txt`, `usage_log.csv`

**Method:** Diffed the working tree against `ff3e25e`; re-read every changed file; re-ran the
offline tool tests; cross-checked every numeric and factual claim in `report.md` against
`eval_results.txt` line by line. **No API calls were made.**

---

## Verdict

**~97% complete.** Every acceptance criterion in both source documents now has evidence behind it,
and revision 2's headline problem — a write-up contradicting its own evidence file — is fully
resolved. `report.md` is now internally consistent and accurate.

One new issue was introduced in the process, and it matters more than its size suggests: **the
system prompt now contains a hardcoded instruction written to make a specific eval case pass** —
the same anti-pattern the write-up holds up as its central improvement. That should be reverted
before delivery.

| Task | Rev 2 | Now |
|---|---|---|
| Build baseline document Q&A CLI | Complete | **Complete** |
| Centralize tier routing and costs | Complete | **Complete** |
| Return validated structured JSON | Complete | **Complete** |
| Add resilient document retrieval | Coverage regression | **Complete** |
| Verify end-to-end Q&A | Write-up stale | **Complete** — see §2.1 caveat |

---

## 1. Fixed since revision 2

| Rev 2 finding | Resolution | Verified |
|---|---|---|
| **§3.1** `report.md` cost table stale (50 / $0.164071 vs 51 / $0.17380900) | Regenerated | **All six figures match `eval_results.txt` exactly.** 53 / $0.189991 routed, 46 / $0.252830 flagship, 16 / $0.026337 forced-cheap, savings $0.062839. Recomputed the percentage: 24.86% ✓ |
| **§3.1** Write-up claimed "none observed" while the evidence showed a chain deviation | Rewritten around the real finding: *"two complex retrieval tasks ended at zero confidence and one skipped the expected full-read chain"* | Matches the three degradation notes in `eval_results.txt` ✓ |
| **§3.2** Missing-*file* read case removed from the eval | Added back as case 9 (`edge-missing-file`), bringing the suite to 11 cases — the missing-*section* case was kept | Live trace: `read_doc("missing_policy.txt")` → `confidence: 0.0` ✓ |
| **§3.3** Prompt before/after described but not shown | Both blocks now quoted verbatim in `report.md` | ✓ — but see §2.2 |
| **§3.4** `schema_failures` conflated execution errors with schema failures | Now gated on `record["status"] == "passed" and record.get("schema_valid") is False` | ✓ |

Every factual claim in `report.md` was re-verified against the results file. All check out:

- *"Five of six routed easy/complex cases executed the full list-search-read chain; the remaining
  simple core-hours lookup answered directly from a sufficient search snippet"* — case 1's trace is
  `list_docs → search_docs`, no read, `confidence: 1.0` with a correct grounded quote. Accurate.
- *"All five edge and out-of-bounds cases … failed safely with confidence 0.0"* — cases 7–11, all
  `0.0`. Accurate.
- *"This is evidence for routing, not a claim that either tier behaves deterministically on every
  run"* — a fair, well-judged caveat. Keep it.

---

## 2. New issues in the uncommitted changes

### 2.1 The prompt now hardcodes behaviour for one eval case — **revert before delivery**

`prompts.py` gained:

```text
When a user explicitly asks to test retrieval error handling for a named
missing file, call read_doc with that filename and report the returned error.
```

It exists solely to make eval case 9 fire a `read_doc` on a missing file. That is the same class of
change as the travel shortcut removed in `cc217f3` — and `report.md`'s "Prompt evolution" section
presents removing exactly that kind of shortcut as the project's key prompt improvement:

> "This removes hidden filename and policy assumptions…"

So the deliverable now argues against itself: it showcases the deletion of a hardcoded retrieval
shortcut, in a prompt that has just acquired a new one. If a reviewer opens `prompts.py` during the
demo, that is the question you get.

**It compounds.** The eval question is itself instruction-shaped —
*"For a retrieval error-handling test, call read_doc on missing_policy.txt and report the result."*
It names both the tool and the file. The resulting trace is a bare `read_doc("missing_policy.txt")`
with no `list_docs` first. Between the prompt line and the question phrasing, case 9 now tests
**obedience, not resilience**.

Worth noting: the *original* phrasing produced better agent behaviour. In the earlier run the model
called `list_docs()`, saw the file was not listed, and refused without a pointless read — which is
what a good retrieval agent should do. The acceptance criterion only requires that *"a `read_doc`
call for a missing file completes without an unhandled failure"*; it does not require the model to
be goaded into making one.

**Recommended fix:** revert the prompt line, then either

- keep case 9 with natural phrasing (*"What does missing_policy.txt say about vacation?"*) and
  accept a `list_docs`-then-refuse trace as a pass, or
- drop the e2e case and rely on `test_phase3.test_local_tools`, which already asserts
  `read_doc("missing_policy.txt") == "Error: Document or section not found."` — verified passing.

Either way the criterion stays satisfied and the prompt stays honest.

### 2.2 `AGENT_PROMPT_VERSION` was not bumped

`prompts.py:5` still reads `AGENT_PROMPT_VERSION = "agent-v2"`, but the prompt text changed. Both
`eval_results.txt` ("Agent prompt version: agent-v2") and `report.md` label this run agent-v2, and
the "after" prompt quoted in `report.md` **omits the new line** — so the write-up's before/after
does not show the prompt that actually produced the results.

The point of a version constant is that it identifies the prompt. Bump to `agent-v3` and re-quote —
or apply §2.1's revert, at which point the prompt genuinely *is* v2 again and everything reconciles
with no further edit.

### 2.3 `_enforce_retrieval_refusal` was broadened — over-refusal is now reachable

`agent.py` changed from:

```python
if no_matching_evidence and response.source_quote == "N/A" and response.confidence > 0.0:
```

to:

```python
if (no_matching_evidence or tool_error_seen) and response.confidence > 0.0:
```

Dropping the `source_quote == "N/A"` guard removes the condition that confined the override to
answers the model had *already* marked ungrounded. It can now zero out a genuinely grounded answer.

**Concrete scenario:** the model searches, gets zero hits, falls back to `read_doc(filename)` on the
full document (which the prompt explicitly tells it to do), finds the answer, and returns a real
supporting quote. `no_matching_evidence` is still `True` — `zero_hit_seen=True` and
`search_hit_seen=False`, because no search ever succeeded — so **confidence is silently forced to
0.0 despite a valid quote.** The same applies to `tool_error_seen`: one failed tool call anywhere in
the run now zeroes the final confidence even if the model recovered from it.

This did not fire in the current run, but it is a live path and would read as a correctness bug in
the demo. **Fix:** restore the `source_quote == "N/A"` condition, or additionally require that no
successful `read_doc` occurred.

---

## 3. Standing observations

### 3.1 The cost-savings figure is unstable across runs

Same suite, three consecutive runs:

| Run | Routed | Flagship-only | Savings |
|---|---:|---:|---:|
| 13:41 | $0.164071 | $0.291125 | **43.6%** |
| 15:09 | $0.173809 | $0.289915 | **40.1%** |
| 16:13 (current) | $0.189991 | $0.252830 | **24.9%** |

A 19-point swing on essentially the same questions. `report.md` handles this honestly with its
determinism caveat, which is the right call — but a single number in a table headed "Measured cost"
invites being read as precise, and "routing saves 24.9%" is a materially different claim from
"routing saves 43.6%".

There is a genuinely interesting finding buried here, worth a sentence in the write-up: **savings
erode when the cheap tier flails.** This run had the worst cheap-tier performance (all three
complex cases flagged) and the lowest savings — because a cheap model that retries and re-searches
burns turns. Cheap-tier failure is not only a quality cost; it eats the cost advantage that
justifies routing in the first place. That is exactly what the "where the cheap tier fell apart"
criterion is fishing for.

**Suggested fix:** report the observed range (25–44% across three runs), or average three runs,
rather than presenting one run's number as *the* saving.

### 3.2 `chain_ok` conflates "didn't need to chain" with "failed to chain"

`eval_results.txt` reports "Tool-chain reliability: 5/6", and the one miss is case 1 answering
correctly from a search snippet without needing a full read — ideal behaviour, scored as a failure.
`report.md` explains this correctly in prose, but the raw metric reads worse than reality. Consider
scoring the chain only on cases that actually require a full-text read.

### 3.3 Minor, carried forward

- `[SCHEMA VALIDATION FAILED]` still prints to **stdout** in `agent.py`, which `eval_suite.run_case`
  captures into `tool_trace` via `redirect_stdout`. Harmless at 0 failures; would pollute traces
  when it fires. Prefer stderr.
- `_response_from_content` discards the malformed text rather than preserving it in
  `metadata["schema_error"]`.
- `list_docs()` reports `type: "text"` for every file and derives `date` from the first `20xx`
  string in the body, falling back to mtime.
- The agent path validates post-hoc rather than using SDK structured-output enforcement.
  Defensible, and now measured — 25/25 valid this run.

### 3.4 Everything is uncommitted

All of the above sits in the working tree; `git status` shows seven modified files against
`ff3e25e`. Commit before the demo so the delivered state is reproducible.

---

## 4. Current evidence base

| Artifact | State |
|---|---|
| `eval_results.txt` | 11 routed + 11 flagship-only + 3 forced-cheap = 25 case-runs. Routing 6/6, chain 5/6 (see §3.2), refusal safety 5/5, schema failures 0 |
| `report.md` | ~half a page. Cost table, prompt before/after shown verbatim, cheap-tier degradation identified, determinism caveat. **Fully consistent with `eval_results.txt`** |
| `README.md` | Setup, both entry points, tests, eval — accurate against current CLI behaviour |
| `DEMO_RUNBOOK.md` | 5 steps covering Q&A flow, routing, structured JSON, retrieval trace, failure handling, cost comparison |
| `usage_log.csv` | 1,272+ rows; the tier/model split evidences the config-only model swap (4 legacy `gpt-4o*` rows) |
| `phase3_results.json` | Regenerated 13:22, consistent with current code |

---

## 5. Remaining work

Small, and mostly subtractive:

1. **Revert the eval-specific prompt line in `prompts.py`**, and re-phrase or drop eval case 9
   accordingly. *(§2.1)* — the one item to treat as blocking.
2. **Restore the `source_quote == "N/A"` guard** in `_enforce_retrieval_refusal`. *(§2.3)*
3. **Re-run `eval_suite.py` once** after 1 and 2, and refresh `report.md`'s table from it.
4. **Report the savings as a range** across runs, and add the "cheap-tier failure erodes the cost
   advantage" observation. *(§3.1)*
5. **Commit.** *(§3.4)*

If §2.1 is reverted, `AGENT_PROMPT_VERSION = "agent-v2"` becomes correct again and §2.2 resolves
itself with no edit.

**Demo caveat, unchanged:** a full `eval_suite.py` run is ~115 API calls across three modes and
appends to the committed `usage_log.csv`. Regenerate once, freeze the numbers into `report.md`, and
do not re-run live during the demo.
