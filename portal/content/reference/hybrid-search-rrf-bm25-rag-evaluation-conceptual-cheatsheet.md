---
title: Hybrid Search, RRF, BM25 & RAG Evaluation Conceptual Cheatsheet
description: A conceptual guide covering BM25, vector search, Reciprocal Rank Fusion (RRF), and RAG evaluation metrics.
owner: fa
updated: '2026-08-25'
tags:
  - ai-strategy
  - rag
  - llm
  - machine-learning
  - reference
status: published
visibility: internal
reviewCycleMonths: 6
order: 50
related: []
---

1. High-Level Search Architecture Comparison

| Search Paradigm | Mechanism & Concept | Primary Strengths | Primary Weaknesses | Best Suited For |
| :--- | :--- | :--- | :--- | :--- |
| **Sparse / Lexical (BM25 / FTS)** | Exact term matching via inverted indices, TF-IDF, and BM25 scoring. Functions like a book index by looking up explicit keywords. | Exact keywords, proper nouns, project codes, SKU IDs, low latency | Vocabulary mismatch, synonym unawareness, fails on rephrased queries | Specific entity lookup, technical jargon, codes |
| **Dense / Semantic (Vector Search)** | Maps text to dense vector spaces using neural embeddings and measures similarity via cosine or dot product distance. Functions like an expert librarian who understands overall topic context. | Conceptual understanding, semantic similarity, rephrasings, cross-lingual | Misses exact strings, poor on rare codes/numbers, chunk size dependent | Broad intent, conceptual Q&A, natural language search |
| **Hybrid Search (Sparse + Dense)** | Parallel retrieval merged via Rank Fusion algorithms like RRF. Combines the exact index lookup with conceptual topic matching. | Combines exact precision with semantic context; best overall recall | Slightly higher latency, dual indexing overhead | Production RAG systems, enterprise search |

---

## 2. Sparse Retrieval & BM25 Deep Dive

### What is BM25 (Best Matching 25)?
BM25 is a non-linear TF-IDF variation that scores document relevance based on matching query terms while accounting for term frequency saturation and document length normalization. 

If a document mentions a search term 100 times, it is not 100 times more relevant than one mentioning it 5 times; after a few mentions, additional occurrences provide diminishing returns (Term Frequency Saturation). Similarly, a short 1-page document with 3 occurrences is far more focused on that topic than a 500-page manual containing those same 3 occurrences (Length Normalization).

### The BM25 Formula
For a query $Q$ containing terms $q_1, q_2, \dots, q_n$ and document $D$:

$$\text{Score}_{\text{BM25}}(D, Q) = \sum_{i=1}^{n} \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}$$

*   **$f(q_i, D)$**: Term frequency of $q_i$ in document $D$.
*   **$|D|$**: Length of document $D$ (in words/tokens).
*   **$\text{avgdl}$**: Average document length across the entire corpus.
*   **$k_1$ (Term Frequency Saturation)**: Controls how quickly extra occurrences of a term diminish in marginal value (typically set between $1.2$ and $2.0$).
*   **$b$ (Length Normalization)**: Controls how much penalty long documents receive (typically set to $0.75$).

### Inverse Document Frequency (IDF)
$$\text{IDF}(q_i) = \ln \left( \frac{N - n(q_i) + 0.5}{n(q_i) + 0.5} + 1 \right)$$
*   **$N$**: Total number of documents in corpus.
*   **$n(q_i)$**: Number of documents containing term $q_i$.

Common terms like "the" or "is" appear in almost every document and carry virtually no search value (low IDF). Unique or rare terms like "photosynthesis" or "error_code_404" appear infrequently across the collection, making them high-value signals (high IDF).

### Postgres Full-Text Search (FTS) Mechanics
PostgreSQL supports native lexical search via inverted `tsvector` indices. Text is parsed into normalized, stemmed tokens while stripping stop words like "a" or "the" (`to_tsvector`). Words are reduced to their root forms so that variations like "running", "runs", and "ran" map to a single token. Incoming user queries are converted into formatted search predicates (`plainto_tsquery`), and matching documents are ranked using cover density scoring functions (`ts_rank_cd`).

---

## 3. Vector Search (Dense Retrieval)

### Mechanics
*   **Embedding Generation**: Text chunks pass through neural embedding models to generate high-dimensional floating-point vectors. Sentences are plotted as coordinates in a high-dimensional space where concepts with similar meanings sit near each other regardless of shared wording.
*   **Indexing**: Vectors are indexed using approximate nearest neighbor (ANN) structures like HNSW (Hierarchical Navigable Small World) or IVFFlat. Rather than scanning every vector in the database, ANN builds navigation routes to jump directly to the target vector neighborhood.

### Distance & Similarity Metrics
*   **Cosine Similarity**: Measures the angle between two non-zero vectors bounded in $[-1, 1]$. Evaluates whether two pieces of text point in the same directional topic, irrespective of document length.
    $$\text{Cosine Sim}(A, B) = \frac{A \cdot B}{\|A\| \|B\|}$$
*   **Dot Product / Inner Product**: Measures direction and magnitude; identical to Cosine Similarity when vectors are $L_2$-normalized.
*   **Euclidean Distance ($L_2$)**: Measures the straight-line geometric distance between two points in $N$-dimensional space. Shorter distances indicate higher contextual similarity.

---

## 4. Hybrid Search & Reciprocal Rank Fusion (RRF)

### Why Score Blending Fails
Vector search produces bounded similarity scores (e.g., $[0, 1]$), while BM25 outputs unbounded non-negative scores ($[0, \infty)$). Because raw scores come from entirely different mathematical distributions, adding them directly is ineffective—it is akin to combining measurements in Fahrenheit and kilograms without conversion.

### Reciprocal Rank Fusion (RRF)
RRF bypasses raw score scaling by evaluating relative leaderboard positions (ranks). It assigns a reciprocal score based on an item's 1-based rank position in each retrieved list and sums them up.

$$\text{RRF\_Score}(d \in D) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$

*   **$M$**: Set of search systems (e.g., $M = \{\text{Vector}, \text{BM25}\}$).
*   **$r_m(d)$**: The 1-based rank position of document $d$ in search system $m$.
*   **$k$**: Smoothing constant (typically **$k = 60$**), which prevents top-ranking outliers in one list from dominating if they perform poorly in another.

If a document ranks near the top of both keyword search and vector search, its combined reciprocal score increases significantly due to cross-system agreement.

### Worked Conceptual Example of RRF

Suppose a query fetches candidate documents from Vector and Sparse search (top-4 candidates each):

| Chunk ID | Vector Rank $r_{\text{vec}}$ | Sparse Rank $r_{\text{sparse}}$ | Vector Term $\frac{1}{60 + r}$ | Sparse Term $\frac{1}{60 + r}$ | Combined RRF Score |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Doc A** | 1 | 4 | $\frac{1}{61} \approx 0.01639$ | $\frac{1}{64} \approx 0.01563$ | **0.03202** (2nd) |
| **Doc B** | 2 | Not retrieved ($>4$) | $\frac{1}{62} \approx 0.01613$ | $0$ | **0.01613** (3rd) |
| **Doc C** | 3 | 1 | $\frac{1}{63} \approx 0.01587$ | $\frac{1}{61} \approx 0.01639$ | **0.03226** (1st/Top) |
| **Doc D** | Not retrieved ($>4$) | 2 | $0$ | $\frac{1}{62} \approx 0.01613$ | **0.01613** (3rd) |

*Resulting Top RRF Hierarchy*: **Doc C** (0.03226) $\rightarrow$ **Doc A** (0.03202) $\rightarrow$ **Doc B / Doc D** (0.01613).

---

## 5. RAG Evaluation Metrics & Benchmarking

Evaluating RAG systems requires separating Retrieval Quality (finding relevant source material) from Generation Quality (producing valid answers).

### Retrieval Metrics
*   **Recall@k**: Measures the fraction of ground-truth relevant documents captured within the top $k$ retrieved results. Determines if all target documents were successfully collected.
    $$\text{Recall@k} = \frac{|\text{Retrieved}_k \cap \text{Relevant}|}{|\text{Relevant}|}$$
*   **Precision@k**: Measures the proportion of the top $k$ retrieved chunks that are genuinely relevant. Indicates how cleanly the system isolates useful information versus background noise.
    $$\text{Precision@k} = \frac{|\text{Retrieved}_k \cap \text{Relevant}|}{k}$$
*   **Mean Reciprocal Rank (MRR)**: Evaluates how close to the top position the first relevant document appears across a query set $Q$. Measures how quickly a user encounters their first correct match.
    $$\text{MRR} = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$
*   **Hit Rate@k**: Binary metric indicating whether at least one relevant chunk exists within the top $k$ retrieved results.
*   **NDCG@k (Normalized Discounted Cumulative Gain)**: Evaluates retrieval order, applying logarithmic penalties when relevant documents appear lower in the result list.

### Generation Metrics (The RAG Triad)
*   **Context Relevance**: Evaluates whether retrieved context is relevant to the query and free of irrelevant noise.
*   **Groundedness / Faithfulness**: Evaluates whether generated answers are strictly derived from the retrieved context without hallucinating facts.
*   **Answer Relevance**: Measures how directly the generated output addresses the user's initial prompt.

### Mechanical Guardrails & Safety
*   **Quote Faithfulness (`quote_grounded`)**: Mechanically normalizes whitespace and verifies that output `source_quote` strings exist as explicit substrings of corpus documents.
*   **Refusal Verification**: Asserts that out-of-corpus queries force zero-confidence outputs or structural refusals rather than fabricated facts.
*   **Indirect Prompt Injection Resistance**: Evaluates model resistance when retrieved context contains hidden adversarial instructions.
