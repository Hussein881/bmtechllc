# Performance Write-Up

The final Phase 4 evaluation ran 11 routed questions, the same 11 questions on
the flagship tier, and the three complex questions forced to the cheap tier.
The complete responses, tool traces, token counts, and cost records are in
`eval_results.txt`.

## Prompt evolution

The original prompt contained a policy-specific retrieval shortcut:

```text
For reimbursement and travel questions, use the search query exactly
"reimbursement travel" after list_docs(), then read the matching
"Travel & Expense Reimbursement" section from the relevant document.
```

The versioned `agent-v2` prompt replaced it with a generic rule:

```text
Use the filename and location returned by search_docs. If a result has no exact
section title, call read_doc(filename) without a section to inspect the full
matching document. You may repeat searches or reads when needed, but do not
invent filenames or facts.
```

This removes hidden filename and policy assumptions while preserving the
`list_docs → search_docs → read_doc` retrieval workflow.

## Model, cost, and observed quality

The configured rates are verified against the [OpenAI model catalog](https://developers.openai.com/api/docs/models): `gpt-5.6-luna` is $1.00 input / $6.00 output per million tokens, and `gpt-5.6-sol` is $5.00 input / $30.00 output per million tokens. All calculations derive from `config.MODEL_TIERS`.

| Execution mode | API calls | Measured cost |
| --- | ---: | ---: |
| Routed production behavior | 55 | $0.188662 |
| Flagship-only, real run | 47 | $0.301855 |
| Forced cheap, complex cases | 18 | $0.026588 |

This run saved $0.113193, or about 37.5%, against the measured flagship-only
run. It selected the intended tier for all six easy/complex cases, and all
three cases that required full-text retrieval completed the
`list_docs → search_docs → read_doc` sequence. All five edge and
out-of-bounds cases failed safely with confidence `0.0`; the missing-file case
is a natural library lookup, while the direct missing-file tool error remains
covered by `test_phase3.py`.

Every routed final response parsed into `QAResponse`; no schema-validation
failures occurred. The forced-cheap complex run completed without a failure in
this sample, but prior repeated runs recorded zero-confidence and chain
deviations. Across the observed runs, routing savings ranged from roughly 25%
to 44%. Extra searches and retries by a cheaper model reduce both answer
reliability and the cost advantage, so this range is more useful than treating
one benchmark run as a guaranteed saving. This is evidence for routing, not a
claim that either tier behaves deterministically on every run.
