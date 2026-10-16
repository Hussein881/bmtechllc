# Performance Measurement

Run the reviewed company corpus before measuring:

```bash
benchmark-ingest --source-dir data/documents --force --create-indexes
benchmark-evaluate --dataset data/evaluation/golden_queries.json \
  --compare-vector --calibrate-abstention \
  --answers --answer-report artifacts/answer-evaluation.json
```

The output reports search Recall@5 and MRR, filtered-query behavior, selected
cosine/keyword abstention cutoffs, and answer metrics. Answer metrics include
near-miss abstention precision/recall/F1, required-fact coverage, strict
citation-validity rate, and p50/p95 latency. The answer report also aggregates
every logged model call by component and tier: calls, input/output tokens,
latency, actual USD cost, flagship-equivalent USD cost, and routing savings.

The evaluator runs the same cases twice: normal router selection and forced
flagship. Treat the latter as the quality/cost baseline. Do not publish a
numeric result until both runs use the same corpus, golden dataset, configured
models, and price configuration. The calibration sweep considers cosine values
from 0.20 through 0.60 in 0.05 increments and keyword overlap of one or two;
it selects the highest answerable acceptance rate subject to at most 5% false
acceptance among the seven near-miss cases, preferring stricter tied cutoffs.
