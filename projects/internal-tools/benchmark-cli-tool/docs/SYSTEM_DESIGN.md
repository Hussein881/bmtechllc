# System Design: Embedding Architecture

## Purpose

This note explains how the ingestion engine turns documents into searchable
information, and why it currently uses OpenAI's `text-embedding-3-small`
model. It is written for both people deciding how company documents should be
handled and engineers maintaining the pipeline.

An **embedding** is a list of numbers that represents the meaning of a piece of
text. Text about similar ideas tends to produce vectors that are close together.
The retrieval engine uses those vectors to find relevant passages even when the
query does not use the same words as the document. The original text remains in
PostgreSQL; an embedding is an additional search aid, not a replacement for the
source text.

## Decision summary

For now, retain the current direct OpenAI integration and do not add LangChain
solely for embeddings. The current solution is small, understandable, and
already compatible with the database schema.

| Approach | What it means | Best fit |
| --- | --- | --- |
| Current recommendation | Local Python processing with OpenAI embeddings | General internal retrieval where external embedding processing is permitted |
| Fully local | Local Python processing with a locally hosted embedding model | Offline, strict data-residency, or no-external-service requirements |
| LangChain | A library that connects pipeline components and providers | Only if the project later needs its wider integrations or workflow abstractions |

LangChain is not an embedding model. It can call OpenAI or a local model, but
the project would still need to select, operate, and evaluate the actual model.

## Recommendation for this project

The recommended next steps, in order, are:

1. Keep the direct `text-embedding-3-small` integration and the existing
   pgvector schema.
2. Do not add LangChain yet. It would add a dependency layer without improving
   the current ingestion or retrieval path.
3. Add controlled document-subject metadata using the embeddings the pipeline
   already creates.
4. Add a calibrated application-level `no_relevant_information` decision before
   presenting search results to end users.
5. Build a small, reviewed evaluation set containing realistic answerable and
   unanswerable queries before considering a different embedding model.

This sequence has the best near-term value for the least additional complexity.
Reconsider a fully local embedding model only if offline operation, privacy,
data residency, or remote-embedding cost become concrete requirements.

## Current embedding implementation

The engine currently uses dense semantic text embeddings from OpenAI's
`text-embedding-3-small` model. Each embedding is a 1,536-dimensional
floating-point vector stored in PostgreSQL's pgvector `vector(1536)` column.
The engine compares query and chunk vectors with cosine distance to identify
semantically similar content.

During ingestion, the embedding input contains a short provenance header—for
example, the source filename and section—followed by the cleaned chunk text.
At search time, the submitted query is embedded with the same model and compared
with those stored chunk vectors. The model name is configurable through
`EMBEDDING_MODEL`, but any replacement must return 1,536 dimensions unless the
database schema and stored embeddings are migrated.

## What happens during ingestion

```text
Source files
  -> local parsing, redaction, cleanup, and chunking
  -> embedding model converts each chunk into a vector
  -> PostgreSQL stores text, metadata, full-text index, and vector
  -> later queries use both full-text matching and vector similarity
```

The local Python code reads the files, removes common credential patterns,
normalizes text, and divides it into manageable chunks. This work happens before
an embedding request is made. The remote model receives chunk text and returns
only a vector; PostgreSQL stores that vector alongside the cleaned chunk text
and its provenance metadata.

At search time, the system runs two complementary searches:

- PostgreSQL full-text search finds literal keywords and related English word
  forms in the stored chunk text.
- pgvector compares the query embedding with stored chunk embeddings to find
  semantically similar passages.

The results are fused by rank. Neither search reads the original source files at
query time.

## Why the current design is recommended

`text-embedding-3-small` is already the engine's configured embedding model,
and its default 1,536-dimensional vectors match the current PostgreSQL
`vector(1536)` column. It provides the semantic-search portion of the existing
hybrid retrieval system without requiring local model hosting or a new framework
layer. [OpenAI's embedding guide](https://developers.openai.com/api/docs/guides/embeddings)
describes embeddings as useful for search, clustering, and classification.

This is a practical default when the organization permits document chunks to be
processed by an external embedding service. It keeps the code path direct:
there is one provider boundary, one model configuration, and one vector format.
The important operational responsibility is to ensure that the documents are
appropriate to send to that provider after local redaction.

Adding LangChain today would make the architecture less direct without changing
retrieval quality, privacy boundaries, or model choice. It becomes worthwhile
only if the project later needs capabilities it brings beyond this pipeline—for
example, a standardized multi-provider integration, complex document-loader
support, or broader workflow composition.

## Subject classification: a useful hybrid extension

The existing `source_type` field is a processing label such as `policy_doc`,
`transcript`, or `discord`; it does not identify what a document is about. If
the product needs subjects such as "software quality assurance" or "process
modeling," add separate semantic metadata rather than repurposing `source_type`.

The recommended design combines remote encoding with a local, explainable
classification decision:

```text
Existing chunk embeddings
  -> locally combine a file's chunk vectors into a document vector
  -> locally compare it with cached vectors for approved subject labels
  -> store primary subject, topic tags, scores, and an unknown/review state
```

Each approved subject should have a short description, not just a bare label.
For example, the prototype for *software quality assurance* could mention
verification, validation, test planning, and agile testing. Embed these label
descriptions once and cache the results. The engine can then compare each
document vector with the label vectors using cosine similarity.

This approach has several advantages:

- It uses embeddings that the ingestion process already created, so it normally
  does not require sending the document a second time.
- The taxonomy stays controlled. It avoids an expanding collection of near-duplicate
  labels such as "QA," "quality assurance," and "software testing."
- The decision is inspectable: retain the best few label scores, then mark a
  weak or ambiguous result as `unknown` or `needs_review` instead of guessing.

Initially, attach the resulting subject metadata to every chunk from the source
file. Add chunk-level subjects only if a significant number of files genuinely
cover multiple unrelated topics.

## Fully local alternative

It is possible to avoid a remote embedding service entirely, but this requires
a real local embedding model. A Python library such as Sentence Transformers can
run one, and LangChain can optionally wrap that model; neither library is the
model itself.

```text
Source files
  -> local parsing, redaction, cleanup, and chunking
  -> locally hosted embedding model
  -> PostgreSQL stores text, metadata, full-text index, and vector
```

Choose this path when offline operation, data residency, or a policy against
sending document text to an external service is a hard requirement. In return,
the project becomes responsible for downloading and updating model files,
providing sufficient CPU or GPU capacity, measuring throughput, responding to
model failures, and proving retrieval quality against a representative test set.

The right choice is therefore driven more by data-handling requirements and
measured search quality than by whether a framework is available.

## Query handling and retrieval quality

### Current behavior

The current retrieval API accepts any non-empty query string without selecting
keywords, rewriting it, shortening it, or splitting it into smaller questions.
It uses that same raw string in both retrieval modes:

- **Full-text search (FTS)** passes the query to PostgreSQL
  `websearch_to_tsquery('english', ...)`. PostgreSQL normalizes words, removes
  English stop words, and applies web-search syntax. Unquoted terms are combined
  with `AND`; quoted text is treated as a phrase; `OR` offers alternatives; and
  a leading dash excludes a term. This means a long unquoted sentence can become
  too restrictive for FTS because every surviving term must appear in one chunk.
  [PostgreSQL's FTS documentation](https://www.postgresql.org/docs/current/textsearch-controls.html)
  describes these parsing rules.
- **Vector search** sends the whole query unchanged to
  `text-embedding-3-small` and searches for the closest stored chunk vectors.
  A long, multi-topic query can produce a broad vector that is less specific than
  a focused question.

Hybrid retrieval embeds the query first, then retrieves the top 20 vector and
top 20 FTS candidates concurrently and fuses their ranks with Reciprocal Rank
Fusion (RRF). When FTS finds no match, vector candidates still appear in the
result. The engine does not currently apply a relevance threshold, rerank the
fused candidates, produce an answer, or return a `no_relevant_information`
outcome.

There is no project-defined length limit. `text-embedding-3-small` accepts up
to 8,192 input tokens, so an over-limit hybrid or vector query fails at the
embedding request; hybrid retrieval then fails before FTS begins. FTS-only
search does not call the embedding provider, but an excessively long all-AND
query will commonly have no match and can take more database work. See the
[OpenAI embeddings guide](https://developers.openai.com/api/docs/guides/embeddings)
for the model input limit.

### Common production RAG pattern

There is no single mandatory industry standard, but production RAG systems
commonly use this sequence:

```text
Validate and normalize the query
  -> identify simple versus long or multi-part requests
  -> retrieve with keyword and vector search in parallel
  -> rerank the candidate chunks for query-specific relevance
  -> decide whether evidence is sufficient
  -> return sourced results or an explicit no-result outcome
```

Hybrid keyword and vector retrieval with RRF is a widely used foundation because
keyword matching preserves exact names, codes, and dates while vectors find
conceptually related wording. [Azure's hybrid-search overview](https://learn.microsoft.com/en-us/azure/search/hybrid-search-overview)
describes this parallel retrieval and fusion pattern. For complex, multi-part
questions, systems may use query decomposition to retrieve for each sub-question
separately; this can improve coverage but adds cost and latency. [AWS's query
decomposition guidance](https://docs.aws.amazon.com/bedrock/latest/userguide/kb-test-config.html)
describes that trade-off. A reranker can then evaluate the query and candidate
chunk text together to improve the final ordering. [AWS's reranking guidance](https://docs.aws.amazon.com/bedrock/latest/userguide/rerank.html)
explains this second-stage role.

### Recommended evolution

Improve this project in the following order:

1. Set a user-facing query token limit below the provider maximum and return a
   clear error rather than allowing an embedding request to fail unexpectedly.
2. Add an evidence-based `no_relevant_information` decision using a reviewed
   evaluation set. Do not treat an RRF score as a confidence score.
3. Add a reranker over the existing hybrid candidate pool.
4. Add query rewriting or decomposition only for queries shown to be long,
   multi-intent, or otherwise poorly served by the direct path.

The exact thresholds, candidate counts, and long-query trigger should be tuned
against representative answerable and unanswerable queries rather than copied
from another system.

## Changing embedding models safely

An embedding-model change is a data migration, not a simple configuration
change. Different models can return vectors with different lengths and will rank
documents differently. A safe migration requires:

1. Evaluate the proposed model with representative retrieval and no-result
   queries before changing production data.
2. Update the PostgreSQL vector column and index definition if its dimensions
   differ from the current 1,536 dimensions.
3. Clear or version the existing embeddings, then re-embed every chunk with the
   new model.
4. Rebuild the pgvector index and re-run retrieval evaluation before relying on
   the new results.

Until those checks demonstrate that a local model meets the required quality and
operational needs, the direct `text-embedding-3-small` integration remains the
recommended design.
