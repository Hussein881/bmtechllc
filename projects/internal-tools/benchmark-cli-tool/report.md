# Performance Write-Up

The Phase 4 benchmark ran 10 routed questions, the same 10 questions forced to
the flagship tier, and the three complex questions forced to the cheap tier.
The complete traces, responses, and per-call telemetry are in
`eval_results.txt`.

## Prompt evolution

The first agent prompt embedded travel-specific retrieval behavior. The current
versioned `agent-v2` prompt in `prompts.py` instead instructs the model to use
document metadata and search locations generically, then to read the full
document if there is no exact section title. This removes filename and
policy-specific assumptions while retaining the ordered retrieval workflow.

## Model, cost, and observed quality

The configured tier rates are verified against the [OpenAI model catalog](https://developers.openai.com/api/docs/models): `gpt-5.6-luna` is
$1.00 input / $6.00 output per million tokens, and `gpt-5.6-sol` is $5.00
input / $30.00 output per million tokens. The measured comparison derives all
rates from `config.MODEL_TIERS`.

| Execution mode | API calls | Measured cost |
| --- | ---: | ---: |
| Routed (production behavior) | 50 | $0.164071 |
| Flagship-only (real run) | 45 | $0.291125 |
| Forced cheap, complex cases | 16 | $0.024573 |

Routing saved $0.127054 against the measured flagship-only run (about 43.6%).
The router selected the expected tier for all six easy/complex cases. All six
retrieval lookups requiring source detail followed the `list_docs → search_docs
→ read_doc` sequence, and all four edge/out-of-bounds cases safely returned a
zero-confidence refusal.

Every routed result parsed into `QAResponse`; schema-validation failures were
zero. The forced-cheap complex run did not show a tool-chain, JSON, or answer
completion failure in this sample, so the current evidence records “none
observed,” rather than claiming the cheap tier is universally equivalent. The
suite retains that stress run specifically to make future degradation visible.
