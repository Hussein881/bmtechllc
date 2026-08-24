---
title: RAG Architecture & Production Best Practices
description: A reference guide for production RAG systems covering document chunking strategies, hybrid retrieval, re-ranking, prompt grounding, and evaluation metrics.
tags: [rag, llm, ai-strategy, reference]
status: draft
visibility: internal
owner: ah
updated: 2026-08-17
reviewCycleMonths: 6
order: 50
related: [evaluating-rag-quality]
---

Building a great RAG system is about more than plugging a vector database into an LLM. The most effective production deployments combine clean data pipelines, strong retrieval strategies, thoughtful context assembly, and continuous evaluation to deliver accurate, grounded answers at scale.

---

## 1. Data Preprocessing & Ingestion

### Chunking Strategy

* **Do** favor semantic chunking based on document structure—headings, sections, code blocks, and paragraphs—instead of relying on arbitrary character limits.
* **Do** aim for chunks between **250–500 tokens** with **10–20% overlap** to maintain a strong balance between context preservation and retrieval precision.
* **Do** adjust chunk size based on content type, as technical documentation, code, and long-form articles often benefit from tailored chunking approaches.

### Metadata Enrichment

* **Do** enrich each chunk with metadata such as:
  * Document title
  * Section or heading name
  * Creation or update timestamps
  * Access permissions
  * Source URLs
* **Do** leverage rich metadata to improve filtering, ranking, traceability, and source attribution throughout the retrieval pipeline.

### Pipeline Hygiene

* **Do** remove boilerplate content, navigation elements, duplicated text, and other noise before generating embeddings.
* **Do** maintain synchronization between source repositories and vector indexes.
* **Do** implement deduplication and refresh mechanisms; **don't** allow stale or redundant content to appear in retrieval results.

---

## 2. Retrieval & Search Optimization

### Hybrid Search

* **Do** combine **dense vector search** with **sparse keyword search (BM25)**. [More info here](https://paths.grasp.study/modules/7c1656ed-8e58-4430-a363-5cf010a00cda/lessons/1d2dc4d9-804b-43e4-9cdb-21938f6d0803).
* **Do** rely on semantic retrieval to capture intent and meaning, while using keyword retrieval for exact matches like:
  * Product names
  * Acronyms
  * Error codes
  * Technical identifiers
  * Exact-match terminology
* **Don't** rely solely on single-retrieval methods, as hybrid approaches consistently outperform either method in isolation.

### Query Enhancement

#### Query Rewriting & Expansion

* **Do** rewrite complex user questions into simpler sub-queries.
* **Do** generate synonymous or related search terms to improve recall.
* **Do** expand abbreviated or ambiguous queries when appropriate.

#### HyDE (Hypothetical Document Embeddings)

* **Do** generate a hypothetical answer to the user's question, embed that synthetic response, and use it to retrieve contextually similar real documents.
* **Do** apply this technique to improve retrieval quality for complex or poorly worded queries.

### Two-Stage Retrieval & Re-ranking
* **Stage 1: Candidate Retrieval**
  * **Do** retrieve a broad candidate set (typically **20–50 documents**) using fast vector or hybrid search to maximize recall.

* **Stage 2: Re-ranking & Selection**
  * **Do** pass candidate documents through a specialized re-ranking model (such as Cross-Encoders, Cohere Rerank, or other specialized ranking models) to re-score relevance.
  * **Do** select the highest-quality **3–5 documents** from the re-ranked pool for the final context window.

* **Do** adopt this two-stage approach to improve precision while maintaining strong recall.

---

## 3. Context Assembly & Generation

### Mitigating the "Lost in the Middle" Problem

Large language models tend to pay more attention to information located at the beginning and end of a context window.

* **Do** place the highest-confidence passages near the top of the prompt.
* **Do** position additional critical evidence near the end.
* **Don't** bury essential information in the middle of long context blocks.

### Grounded Generation

* **Do** use system prompts that explicitly instruct the model to answer only from retrieved context.
* **Do** require the model to acknowledge when sufficient evidence is unavailable.
* **Don't** allow or encourage unsupported assumptions and speculation.

### Source Attribution

* **Do** include inline citations, references, or structured outputs whenever possible.
* **Do** ensure generated responses can be traced back to original source material.
* **Do** make verification easy for both users and evaluators.

---

## 4. Evaluation, Guardrails & Maintenance

### Evaluate the RAG Triad

* **Do** evaluate a production RAG system across three core dimensions:
	- ***Context Relevance*** - **Do** confirm the correct documents were retrieved and verify that the context actually addresses the user's query.
	- ***Groundedness / Faithfulness*** - **Do** verify that the generated answer accurately reflects the retrieved evidence; **don't** tolerate unsupported claims or hallucinations.
	- ***Answer Relevance*** - **Do** ensure the final response directly solves the user's problem and remains complete, useful, and aligned with user intent.

### Continuous Monitoring

* **Do** treat evaluation as an ongoing process rather than a one-time benchmark. Recommended practices include:
	* **Do** maintain curated golden datasets.
	* **Do** run automated evaluations using tools such as:
	  * Ragas
	  * TruLens
	  * DeepEval
	* **Do** monitor production metrics including:
	  * Retrieval quality
	  * Latency
	  * Embedding costs
	  * Context length growth
	  * User feedback signals
	* **Do** use continuous monitoring to catch and fix regressions before they impact users.

---

## Key Takeaway

The strongest RAG systems are rarely defined by a single model or retrieval technique. Success comes from combining clean and well-structured data, robust retrieval pipelines, grounded generation practices, and rigorous evaluation. When these pieces work together, RAG becomes a reliable mechanism for delivering accurate, explainable, and scalable AI-powered answers.

## References
- https://www.kapa.ai/blog/rag-best-practices
- https://dev.to/satyam_chourasiya_99ea2e4/mastering-retrieval-augmented-generation-best-practices-for-building-robust-rag-systems-p9a
- https://paths.grasp.study/modules/7c1656ed-8e58-4430-a363-5cf010a00cda/lessons/1d2dc4d9-804b-43e4-9cdb-21938f6d0803
