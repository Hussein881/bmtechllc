# Completeness Assessment — `benchmark-cli-tool`

**Date:** 2026-08-06
**Scope:** `bmtechllc/projects/internal-tools/benchmark-cli-tool`
**Assessed against:** *Week 1 Deliverables* and *Build baseline document Q&A CLI* (task breakdown with acceptance criteria)

**Method:** Read every source file in the project; ran the offline (non-API) portions of the tool
and test suite directly; audited `usage_log.csv` (901 rows), `eval_results.txt`,
`phase3_results.json`, and the git history. **No API calls were made** during this assessment —
doing so would spend money and append rows to the committed cost log.

---

## Verdict

**~85% complete.** All four coding tasks are implemented and backed by evidence of real API runs.
The architecture matches the brief closely: a single `llm.py` gateway, a tier config, a
classification router, three retrieval tools, a bounded agent loop, and CSV cost telemetry.

Two deliverables are genuinely missing (the half-page write-up and the demo — both already
unticked in the task document). Beyond those, there is **one currently-failing test** and a set of
correctness and evidence gaps sitting behind criteria that are already marked `[x]`.

| Task | Status |
|---|---|
| Build baseline document Q&A CLI | **Complete** |
| Centralize tier routing and costs | **Complete**, with one single-source-of-truth leak |
| Return validated structured JSON | **Partial** — enforced on the CLI path, not the agent path |
| Add resilient document retrieval | **Complete**, with a section-lookup bug and thin two-tier evidence |
| Verify end-to-end Q&A | **Partial** — eval done, write-up and demo missing |

---

## 1. Criteria that are genuinely met

| Criterion | Evidence |
|---|---|
| CLI accepts one document + one question, prints an answer | `main.py` — accepts positional or `--doc`/`--question`; path-traversal guarded at `main.py:29` |
| Runs on Python 3.11+ with the OpenAI SDK and a working key | `.venv` present; PEP-604 typing and `from __future__ import annotations` throughout; 901 real usage rows spanning 2026-08-03 → 2026-08-06, zero rows with null token counts |
| Answers are grounded in the supplied document | All 10 eval cases return quoted `source_quote` values traceable to `documents/` |
| Every model request passes through `llm.py` | Verified by grep across the project: `llm.py` is the **only** file importing `openai`. `logger.py` mentions it in a docstring only |
| Config maps cheap and flagship tiers to model names | `config.py:25-36` — frozen dataclass with model id + input/output rates per tier |
| Changing a tier's model is a config-only edit | Proven by the log itself: 2 early calls on `gpt-4o-mini`/`gpt-4o`, then 897 on `gpt-5.6-luna`/`gpt-5.6-sol`. Commit `5229839` ("change the tiers inside of config.py") touched configuration only |
| Easy and hard questions route to different tiers; tier is logged | `router.py` classification call; `tier` + `model` columns in `usage_log.csv`; `Selected tier:` printed to stderr at `main.py:75`; `selected_tier` recorded per case in `eval_results.txt` |
| CSV log records token usage and cost per query and tier | `logger.py` — `timestamp, question, tier, model, prompt_tokens, completion_tokens, total_cost_usd`; 901 rows, $2.14 cumulative |
| Provider-specific logic confined to `llm.py` | Including the `reasoning_effort: "none"` GPT-5.6 tool-calling quirk at `llm.py:79` — correctly isolated |
| `list_docs()` returns title, type, date | `tools.py:58-73`; verified live against all 5 documents |
| `search_docs(query)` returns snippets with filename and location | `tools.py:76-105`; location rendered as `"Section (line N)"` |
| `read_doc(filename, section)` returns full text for an existing file/section | `tools.py:108-125`; verified live |
| Retrieval run chains list → search → read in order | 6/6 in `eval_results.txt`, confirmed by the recorded tool traces |
| Zero-hit search and missing-file read complete without unhandled failure | Verified by direct execution — see §2 below |
| Ten test questions answered, easy/hard visibly routed | `eval_results.txt`: routing accuracy 6/6 on easy + complex |
| Workflow refuses gracefully when the answer isn't present | 4/4 edge and out-of-bounds cases return `confidence: 0.0`, `source_quote: "N/A"` |
| Cost log supports a routing-vs-flagship table | Present in `eval_results.txt` — see caveat in §3.2 |
| Secrets hygiene | `.env` is gitignored and untracked; only `OPENAI_API_KEY` present; working tree clean |

### Failure paths I executed directly (all safe, no exceptions)

```
search_docs("quantum relocation allowance")   -> []
read_doc("nope.txt")                          -> "Error: Document or section not found."
read_doc("../config.py")                      -> "Error: Document or section not found."   # traversal blocked
execute_tool("nope", {})                      -> "Error: Unknown tool 'nope'."
execute_tool("read_doc", {"wrong": 1})        -> "Error: Tool 'read_doc' could not be executed: ..."
```

`tools.py:16-22` rejects any filename that isn't a bare basename, so directory traversal is
closed off. `execute_tool` catches `TypeError`/`ValueError`/`OSError` and returns error strings
rather than raising. This part is solid.

---

## 2. Blocking issue: a test currently fails

`test_phase3.py:38-39` asserts:

```python
content = read_doc(sample_hit["filename"], section="Hours")
assert "10:00" in content
```

Running this now produces `AssertionError`. `read_doc("sample_policy.txt", "Hours")` returns
`"Error: Document or section not found."`

**Root cause:** `tools.py:122` matches section titles by **exact** casefolded equality:

```python
if title.casefold() == requested:
```

The real section in `sample_policy.txt` is `Core Working Hours`. There is no substring,
normalised, or fuzzy fallback, so a near-miss title silently degrades to an error string.

**Consequences:**

1. `test_phase3.py` aborts at its first offline assertion and never reaches the two-tier agent
   comparison or the telemetry checks.
2. `phase3_results.json` is **stale** — it was produced by an earlier passing run and no longer
   reflects the current code. Note its recorded trace uses `section: "Hours"`, which today would
   return an error.
3. It's a live risk for the agent, not just the test: the model has to guess section titles
   verbatim, and any imprecision costs a wasted tool call.

**Fix:** add a fallback in `read_doc` — try exact match, then substring/containment match, then
return the full document rather than an error. The agent prompt already tells the model to fall
back to a section-less read, so aligning the tool with that instruction is consistent.

---

## 3. Gaps behind ticked criteria

### 3.1 The agent path does not enforce the JSON schema, and its fallback hides that

`main.py` uses the SDK's parsed API with Pydantic validation (`llm.py:109-122`) — correct and
strict.

But `agent.py` — the tool-calling path that the **entire evaluation runs on** — asks for JSON in
the system prompt (`prompts.py:17-20`) and parses free text. On a parse failure, `agent.py:29`
quietly wraps the raw text as the answer:

```python
except (ValueError, TypeError):
    return QAResponse(answer=content.strip(), confidence=0.0, source_quote="N/A")
```

The brief is explicit on this point: *"Make the output structured JSON and validate it on both
tiers. Smaller models are sloppier with JSON. Find out how, now rather than in production."*

The current fallback makes that failure mode **invisible**. A malformed cheap-tier response is
indistinguishable in the results from a legitimate refusal — both surface as
`confidence: 0.0 / source_quote: "N/A"`. This is the most likely reason `eval_results.txt` reports
"Cheap-tier degradation notes: none observed."

**Fix:** instrument the fallback with a counter or a log line, then re-run the eval. That single
change converts "none observed" from an unsupported claim into real evidence — and it produces
exactly the material the write-up needs.

### 3.2 The "flagship-only" cost column is a repricing, not a run

`eval_suite.py:174-176` re-prices the **routed** token counts at flagship rates:

```python
flagship_cost = sum((cost(row, Decimal("5.00"), Decimal("30.00")) for row in new_rows), Decimal(0))
```

The implementation plan (Phase 4, task 2) calls for executing the suite twice — once with dynamic
routing, once flagship-only. A genuine flagship-only run would produce different token volumes and
potentially different tool paths, so the reported figures are an estimate, not a measurement:

```
Routed execution cost      | $0.19100500
Flagship-only hypothetical | $0.27136500
Estimated savings          | $0.08036000   (~29.6%)
```

**Fix:** either run the suite flagship-only and report measured numbers, or keep the estimate and
label it explicitly as a repricing in the write-up. The header already says "hypothetical" —
the write-up must not drop that qualifier.

### 3.3 Pricing is duplicated outside `config.py`

`eval_suite.py:169-176` hardcodes `Decimal("1.00")`, `"6.00"`, `"5.00"`, `"30.00"` — the same rates
already declared in `config.py:25-36`. Editing a rate in the config silently desynchronises the
cost report, which undercuts the "changing a tier requires only a configuration edit" criterion.

**Fix:** import `MODEL_TIERS` in `eval_suite.py` and derive the rates from it.

### 3.4 Cheap-tier degradation evidence is thin

The criterion "the recorded results note where the cheap tier's tool selection degrades" is ticked,
but there is very little behind it:

- `phase3_results.json` runs **one** question through both tiers and records identical traces for
  each — `["none observed"]` for both.
- In the 10-question eval, the cheap tier only ever handled the 3 easy cases and the 4
  refusal/edge cases. It was never given a hard retrieval task it could plausibly fail.
- The detection logic in `eval_suite.py:187-197` only flags a cheap-tier case as degraded if its
  category is `easy`/`complex` **and** the chain check fails, or if the answer text contains
  "tool-call limit". Since routing sends all complex questions to flagship, cheap is effectively
  only ever measured on the questions it's most likely to get right.

The result is a circular conclusion: routing works, therefore the cheap tier never fails, therefore
there is nothing to write up. The write-up requires the opposite — evidence of where cheap **did**
fall apart.

**Fix:** run the complex cases force-pinned to the cheap tier (`agent.py` already accepts
`--tier`). That is the comparison the brief asks for and the material the write-up is built on.

### 3.5 The missing-file read is only tested with a mock

Eval case 8 ("Read nonexistent_policy.txt...") refuses after calling `list_docs()` alone — the
model correctly notices the file isn't listed and never attempts the read. Sensible behaviour, but
it means the **end-to-end** missing-file `read_doc` path was never exercised live.

That path is covered only by `test_agent_missing_context` (`test_phase3.py:89-146`), which stubs
out `call_llm` entirely with a `SimpleNamespace` fake. The tool-level failure is verified; the
model's handling of a real tool error in a real conversation is not.

**Fix:** add an eval case that names a file which *is* listed but requests a section that doesn't
exist — that forces a genuine tool error into the live loop.

### 3.6 `router.classify_query` crashes on an unparseable label

`router.py:36` raises `RuntimeError` if the classifier returns anything other than `EASY`/`HARD`:

```python
if label_match is None:
    raise RuntimeError(f"Query classifier returned an invalid label: {content!r}. ...")
```

Given that "handles tool failures without crashing" is a stated goal of the week, the routing step
is the one place left where a sloppy cheap-tier response takes the whole CLI down. Defaulting to
`flagship` with a warning would be both safer and more in keeping with the rest of the codebase.

### 3.7 Full document text is written into the committed cost log

`llm.py:30-39` logs the entire last user message into the CSV `question` column. `main.py:48`
constructs that message as:

```python
prompt=f"Document:\n{document}\n\nQuestion:\n{question}"
```

So the **whole document** lands in `usage_log.csv`. Current maximum field length is 456 characters
(from a small synthetic test document), so nothing substantial has leaked yet — but
`usage_log.csv` **is tracked in git**, and running `main.py` against a real client document would
commit that document's full text into the repository history.

**Fix:** truncate the logged question (e.g. first 200 chars), or log only the question segment
rather than the assembled prompt.

### 3.8 Model names and rates need verification against the pricing page

`config.py` uses `gpt-5.6-luna` (cheap, $1.00/$6.00 per 1M) and `gpt-5.6-sol` (flagship,
$5.00/$30.00 per 1M). These are returning valid completions with real token counts, so they are
live models. However, both source documents specifically require model keys taken from the current
OpenAI model list and pricing page, and every cost figure in the deliverable depends on those four
rates being correct.

**Action:** confirm the four rates against the current pricing page before the cost table goes into
the write-up. This is a five-minute check that protects the headline number.

---

## 4. Missing deliverables

These correspond to the three unticked boxes in the task document.

| Missing | Notes |
|---|---|
| **`report.md`** — the half-page write-up | Must contain: where the cheap tier held up vs. fell apart, the cost table, and one prompt before/after improvement. See §3.4 — the supporting evidence doesn't exist yet either |
| **Demo materials** | No script, run sheet, or recording for the 15-minute demo covering Q&A flow, tier routing, structured JSON, retrieval tools, and failure handling |
| **Project `README.md`** | Not in the acceptance criteria, but nothing currently documents how to run `main.py` vs. `agent.py` vs. `eval_suite.py`, or how to set up `.venv` and `.env`. The repo-level `README.md` doesn't cover this project |

**One complication for the write-up:** `prompts.py:5` declares
`AGENT_PROMPT_VERSION = "agent-v2"`, but v1 isn't preserved anywhere in the tree. The
before/after prompt comparison will need to be recovered from git history — likely
`git show 9dcedde:...prompts.py` or the earlier inline prompt in `agent.py`, since `prompts.py`
was extracted during commit `cc217f3` ("finalize phase 4 evaluation and prompt refactor").

---

## 5. Repository hygiene

Good, with one note:

- Working tree is **clean**; all 23 project files are committed.
- `.env` is untracked and correctly ignored (`.gitignore`: `.venv/`, `.env`, `__pycache__/`, `*.pyc`).
- Ten commits with clear conventional-commit messages tracking the phase progression.
- `usage_log.csv` **is** tracked. Commit `ad94f2b` is titled "updated gitignore to include
  usage_log", but it actually **removed** `usage_log.csv` from `.gitignore` and committed the
  1040-line log. That is the right call — the cost log is a required deliverable — but the commit
  message says the opposite of what the commit does. Worth a note so nobody "fixes" it later.
- `.gitignore` omits `eval_results.txt`/`phase3_results.json`, which is also correct: they are
  deliverable artifacts.

---

## 6. Recommended order of work

1. **Fix the `read_doc` section lookup** (add a substring/normalised fallback) — unblocks
   `test_phase3.py` and removes a live agent failure mode. *(§2)*
2. **Point `eval_suite.py` at `config.MODEL_TIERS`** instead of hardcoded rates. *(§3.3)*
3. **Instrument the `agent.py` JSON fallback** with a counter so cheap-tier sloppiness becomes
   measurable. *(§3.1)*
4. **Run the complex cases pinned to the cheap tier**, and either run the suite flagship-only or
   relabel that column as an estimate. *(§3.2, §3.4)*
5. **Re-run `test_phase3.py` and `eval_suite.py`** to refresh `phase3_results.json` and
   `eval_results.txt` against current code.
6. **Verify the four pricing rates** against the OpenAI pricing page. *(§3.8)*
7. **Write `report.md`** using the evidence from steps 3–6, and a project `README.md`.
8. **Prepare the demo run sheet.**

Steps 1–6 are roughly half a day and produce the data that step 7 needs. Steps 3 and 4 are the
ones that turn the write-up from an assertion into an evidenced finding — worth doing before
drafting it.

### Lower-priority cleanups

- Default the router to `flagship` instead of raising on an unparseable label *(§3.6)*.
- Truncate the logged question so documents can't reach the committed CSV *(§3.7)*.
- `llm.py:109` uses `client.beta.chat.completions.parse`; current SDK versions expose this at
  `client.chat.completions.parse`. Works today, but the `beta` namespace will eventually move.
- `list_docs()` sets `type` to the literal `"text"` for every file, and derives `date` from the
  first `20xx` string in the body, falling back to file mtime (`tools.py:68-69`). Functional, and
  it satisfies the criterion, but both fields are crude enough to be worth a sentence in the demo
  rather than a surprise question.
