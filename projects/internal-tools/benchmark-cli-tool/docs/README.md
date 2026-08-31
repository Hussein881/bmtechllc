# Retrieval pipeline notes

This repository is deliberately limited to indexing and evaluating retrieval.
Answer synthesis, chat orchestration, routing, and telemetry are out of scope.

See the [runbook](RUNBOOK.md) for setup, ingestion, live integration testing,
and retrieval evaluation.

See [system flow](SYSTEM_FLOW.md) for the detailed component architecture,
ingestion and retrieval flow, evaluation model, and current limitations.

See [system design](SYSTEM_DESIGN.md) for the embedding-architecture decision,
including the roles of LangChain, OpenAI embeddings, and a fully local option.

Hybrid retrieval retrieves vector and PostgreSQL full-text candidates separately
and combines their ranks with Reciprocal Rank Fusion (RRF), using `k = 60`.
The golden dataset evaluates only chunk retrieval with Recall@5 and MRR.
