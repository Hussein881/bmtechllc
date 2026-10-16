# Client Readiness Assessment

## Verdict

This is a well-structured retrieval prototype, suitable for internal
experimentation or a tightly supervised, non-sensitive pilot. It is not ready
to deploy with a law firm's confidential matter data or as a client-facing RAG
application.

The most accurate label is **pre-pilot foundation, not production-ready**.

## What is already strong

| Area | Assessment |
| --- | --- |
| Retrieval foundation | PostgreSQL, pgvector, full-text search, provenance filters, and parent-context retrieval provide a credible base. |
| Traceability | Results retain source file, chunk position, metadata, and stable content hashes, supporting citations and review. |
| Ingestion | Controlled text, Markdown, and JSON sources retain sections, dates, speakers, and source types. |
| Evaluation | The project includes a reviewed golden set, Recall@5/MRR measurement, and vector-versus-hybrid comparison. |
| Code quality | The offline test suite and lint checks pass. |
| Prompt-injection awareness | Retrieved text is marked and delimited as untrusted, which is a useful start for a future answer layer. |

For an internal knowledge-search tool over approved public documents,
non-sensitive policies, or manuals, this could become a limited pilot without
changing the retrieval architecture.

## Why it is not ready for confidential legal data

The primary gaps are confidentiality, authorization, governance, and
operations—not only retrieval quality.

### No matter-level access control

A law firm needs results restricted by user, office, client, matter, ethical
wall, and document permissions. The existing filename, speaker, and date
filters are search filters; they are not security controls.

The system currently has no:

- authentication or SSO;
- user, role, client, matter, or tenant identity in the schema;
- document-level permission enforcement;
- integration with a document-management system's permissions; or
- audit trail of searches and document access.

As a result, any user able to search the corpus could retrieve any ingested
document. That creates an unacceptable cross-matter disclosure risk.

### External embedding provider

During ingestion, document chunks are sent to OpenAI to create embeddings.
During search, a user's query is also sent. The repository does not contain
controls for data residency, vendor/data-processing review, retention settings,
matter-specific routing, or a validated self-hosted embedding option.

Whether this is acceptable depends on the firm's contracts, client obligations,
jurisdictions, and vendor agreement. Formal security and legal review is needed
before connecting any confidential corpus.

### Prototype-level security and operations

The code redacts a limited set of credential patterns before embedding, but it
does not provide comprehensive PII or data-loss-prevention controls. It also
lacks:

- production secrets and key management;
- audit logging, alerting, and incident response;
- retention, deletion, legal-hold, and records-management workflows;
- backup/restore testing;
- vulnerability/dependency management; and
- rate limits and abuse controls.

The Docker configuration is intentionally local-development-only: PostgreSQL
is exposed on port 5432 and has fixed development credentials.

### Missing legal-document capabilities

Law firms commonly need to search PDFs, scanned documents, email exports, Word
files, exhibits, and document-management-system repositories. The system only
ingests `.txt`, `.md`, and `.json` files. It has no PDF/Office parsing, OCR,
source connectors, document versioning, source synchronization, or deletion
propagation.

The system also does not generate answers, provide an attorney-review workflow,
or preserve page-level citations. It retrieves evidence, but does not yet
provide the attorney-facing workflow required for defensible work product.

### Evaluation is promising but insufficient

The current live result—Recall@5 of 0.95 and MRR of 0.86—is encouraging for
the reviewed lecture-note corpus. It does not establish performance on legal
documents.

The evaluation set contains 30 questions and does not yet measure:

- permissions failures;
- document-version correctness;
- citation or page-level accuracy;
- legal-domain terminology;
- false-positive results for unanswerable questions;
- adversarial or ambiguous queries; or
- load, availability, and recovery behavior.

Hybrid retrieval has also not yet shown an improvement over vector-only search
on the current golden set. Full-text search should remain an active tuning area,
not a production differentiator.

## Adaptability assessment

The architecture is adaptable in useful ways:

- the embedding-provider integration is isolated;
- PostgreSQL stores text, metadata, vectors, and keyword indexes together;
- retrieval already supports provenance metadata and filters; and
- evaluation is built into the workflow.

It is not yet adaptable in the enterprise-critical areas:

- no permissions model to extend;
- no source-connector abstraction;
- no API or service boundary;
- no asynchronous ingestion job system;
- no tenant or matter partitioning;
- a vector schema fixed at 1,536 dimensions, so embedding-model changes need a
  planned migration and full re-embedding; and
- no production deployment or observability configuration.

## Recommended delivery path

### 1. Internal, non-sensitive proof of value

Use only approved non-client documents. Add a small API/UI, PDF/Office
ingestion, and a larger evaluation set built from an approved sample corpus.

### 2. Security and data-governance foundation

Add SSO; role- and matter-based access control enforced in every retrieval
query; document ACL ingestion; immutable audit events; encryption and secrets
management; retention/deletion workflows; and vendor/data-handling review.

### 3. Supervised legal pilot

Limit use to a small practice group and selected matters. Require source
citations and human review. Do not present generated output as legal advice or
final work product.

### 4. Production readiness

Demonstrate permission isolation, backup/restore capability, monitoring, load
behavior, incident response, legal-domain evaluation, and ongoing quality
review.

This phased approach is consistent with the NIST AI Risk Management Framework,
which treats risk management as continuous governance, context mapping,
measurement, and management throughout an AI system's lifecycle.

Reference: [NIST AI RMF Core](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/)
