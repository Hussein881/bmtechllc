# System Overview

## What this system does

This project is a retrieval-only RAG foundation. It prepares local documents
for search, stores text and embeddings in PostgreSQL with pgvector, retrieves
ranked evidence through hybrid search, and measures retrieval quality. It does
not generate answers, call a chat-completion model, or orchestrate agents.

## Ingestion

- Supported source formats are `.txt`, `.md`, and `.json`; PDFs are not
  currently supported.
- Source type is inferred from its path and filename: Discord exports, meeting
  transcripts, or policy/general documents.
- Parsers normalize documents into source units and preserve available
  provenance such as section, speaker, channel, meeting, and date range.
- Before embedding, the engine normalizes text and redacts a limited set of
  credential patterns: OpenAI-style keys, bearer tokens, PEM private keys, and
  simple `password=` assignments. It does not provide comprehensive PII
  detection or redaction.
- Chunks are token-aware, using `cl100k_base`: 400-token target, 500-token
  maximum, 80-token minimum, and up to 50 tokens of overlap. Overlap uses whole
  trailing source units rather than arbitrary text slices.
- The embedding input includes a short provenance prefix, while the stored and
  displayed chunk text stays clean.
- Embeddings use OpenAI `text-embedding-3-small` directly, producing
  1,536-dimensional vectors. Requests are batched and retried.
- Incremental ingestion skips existing SHA-256 chunk-text hashes. `--force`
  replaces chunks for source files supplied to that command.

There is no source-manifest, `--sync`, or `--prune` command. When source files
are deleted or renamed and the database must match the directory exactly,
truncate the chunk table and ingest the corpus again as described in the
[runbook](RUNBOOK.md).

## Storage and indexes

PostgreSQL is the only database; pgvector is a PostgreSQL extension rather than
a separate service. Each chunk stores its text, source location, token count,
JSON metadata, SHA-256 content hash, embedding, and generated full-text
`tsvector`.

- An HNSW cosine-similarity index supports vector search.
- A GIN index supports PostgreSQL full-text search.
- Source, section, and chunk-position indexes support maintenance and
  parent-context reads.

Full-text search runs in PostgreSQL against stored chunk text using the English
`websearch_to_tsquery` configuration. Vector search runs against the pgvector
embedding column.

## Retrieval

Hybrid retrieval is the default. It embeds the query once, retrieves the top 20
vector candidates and top 20 full-text candidates concurrently, deduplicates
them, then ranks the combined set with Reciprocal Rank Fusion (RRF, `k = 60`).
The default response returns the top five chunks.

Search responses include chunk ID, source file, source-relative chunk index,
clean text, metadata, native or RRF score, and `content_sha256`. The hash lets
reviewers create stable evaluation labels without querying the database.

RRF uses candidate positions rather than raw score values, so an RRF score is
not a probability or confidence value. The system has no relevance threshold or
abstention behavior: if full-text search finds no matching terms, vector search
can still return its nearest chunks, even when they are not useful. An explicit
`no_relevant_information` decision policy is not implemented.

Queries are sent unchanged to OpenAI for embedding and PostgreSQL for full-text
search. There is no query rewriting, decomposition, keyword extraction, or
length limit today.

## Parent context

Initial retrieval returns isolated chunks for precision. After identifying a
hit, `benchmark-search --read-doc CHUNK_ID` returns adjacent chunks from the
same source and persisted section. The default window is a contiguous,
hit-centered 1,200-token budget.

The policy-document parser currently treats many colon-ended lines as sections.
For lecture-note-style documents this can make a parent section too narrow; the
retrieval mechanism is implemented, but the section parser needs refinement for
better context grouping.

## Evaluation and telemetry

`benchmark-evaluate` evaluates hybrid retrieval with Recall@5 and MRR for
lookup and multi-chunk questions. Unanswerable questions are included in the
per-query output but excluded from those aggregate metrics because no relevant
chunk exists.

Each evaluation appends one row per query to
`artifacts/retrieval_evaluation.csv` by default. It records retrieval time,
returned chunk IDs, RRF scores, vector-similarity scores, per-query Recall@5,
and run-level Recall@5/MRR. `generation_time_ms` is intentionally blank because
the system does not generate answers.

Golden datasets use durable expected-chunk references: a `source_file` plus the
reviewed chunk's `content_sha256`. The evaluator resolves these to the current
PostgreSQL IDs when it runs. Therefore a truncate and re-ingestion needs no
golden-label update while the reviewed source content is unchanged. If a source
is renamed, a chunk changes, or a chunk is removed, evaluation fails with the
missing reference for manual review.

## Security and current limits

The credential redaction rules reduce the risk of sending common secrets to the
embedding provider, but they are not a full DLP or PII solution. Ingested text
is not currently marked or filtered as untrusted for prompt injection. That has
limited impact while the project only returns retrieval results, but a future
answer-generation layer must treat retrieved text as untrusted data and enforce
instruction/data separation, tool permissions, and output safeguards.

## Recommended direction

Keep the direct OpenAI embedding integration for this project. Adding LangChain
only for embeddings would add abstraction without improving the current path.
Priorities before adding answer generation are a calibrated no-result policy,
stronger PII and prompt-injection controls, improved policy-section parsing,
and a `--sync`/`--prune` ingestion mode.

For operational commands, see the [runbook](RUNBOOK.md). For detailed
implementation behavior, see [system flow](SYSTEM_FLOW.md). For the embedding
architecture decision, see [system design](SYSTEM_DESIGN.md).
