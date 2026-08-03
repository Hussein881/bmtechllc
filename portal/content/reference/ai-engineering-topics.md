---
title: "AI Engineering Guide: LLMs, RAG, Production Systems, and ML Fundamentals"
description: An internal reference covering LLMs, RAG, production AI system design, and ML fundamentals, with a working answer plus one recommended deep-dive resource per topic.
tags: [llm, rag, machine-learning, ai-strategy, reference]
status: draft
visibility: internal
owner: ah
updated: 2026-08-02
reviewCycleMonths: 6
order: 50
related: [agentic-ai-in-38-min]
---

# AI Engineering Guide: LLMs, RAG, Production Systems, and ML Fundamentals

An internal reference covering the questions engineers most often need answered before working on LLM or agentic systems. Each entry gives a working answer plus one recommended resource for going deeper.

**Companion doc:** *Agentic AI — Reference Notes* (design patterns, evaluation, cost, observability, security).

**Suggested reading order if you're starting cold:** §4 ML Fundamentals → §1 LLMs → §2 RAG → §3 Production. If you're already an engineer shipping systems, §1 and §2 are the load-bearing ones.

---

## Table of Contents

1. [Large Language Models](#1-large-language-models)
2. [RAG (Retrieval Augmented Generation)](#2-rag-retrieval-augmented-generation)
3. [System Design & Production AI](#3-system-design--production-ai)
4. [ML & Deep Learning Fundamentals](#4-ml--deep-learning-fundamentals)
5. [Core Reading List](#5-core-reading-list)

---

## 1. Large Language Models

### 1.1 What is a large language model?

A neural network — almost always a Transformer — trained to predict the next token in a sequence. "Token" is a sub-word unit, not a word: *strawberry* may split into several tokens, which is why models are historically bad at character-level tasks like counting letters.

Scale is what makes them useful. Training on trillions of tokens with billions of parameters produces capabilities that weren't explicitly programmed — translation, summarization, code generation, reasoning — as side effects of getting very good at next-token prediction.

Three things to internalize:
- **It is a probability distribution, not a database.** Output is sampled, so the same prompt can give different answers.
- **Knowledge is frozen at training cutoff.** Anything newer must be supplied via context (see §2).
- **The base model is not the assistant.** A base model is an autocomplete engine; post-training turns it into something that answers questions (see 1.2).

**Go deeper:** [Deep Dive into LLMs like ChatGPT — Andrej Karpathy](https://www.youtube.com/watch?v=7xTGNNLPyMI) (3h31m, no math, the single best overview available)

---

### 1.2 How are LLMs trained?

Three stages:

| Stage | What happens | Produces |
|---|---|---|
| **Pre-training** | Next-token prediction over a filtered web-scale corpus (Common Crawl, FineWeb, code, books) | Base model — a knowledgeable autocomplete engine with no conversational behavior |
| **Supervised fine-tuning (SFT)** | Training on curated prompt→response examples written or vetted by humans | Instruction-following assistant |
| **Preference tuning (RLHF/RLAIF/DPO)** | Optimizing against a reward signal derived from human or model preference rankings | Model tuned for helpfulness, tone, and refusal behavior |

Reasoning models add a further reinforcement-learning stage that rewards correct final answers on verifiable problems, which produces long internal chain-of-thought.

Pre-training is where nearly all the knowledge comes from. Post-training mostly shapes *behavior*, not *facts*.

**Go deeper:** [Deep Dive into LLMs like ChatGPT](https://www.youtube.com/watch?v=7xTGNNLPyMI) — the pre-training and post-training sections are the clearest treatment of this pipeline anywhere.

---

### 1.3 What is prompt engineering?

Structuring the input to reliably get the output you need. It is the highest-leverage, lowest-cost tuning method available — always exhaust it before reaching for fine-tuning.

What actually works, roughly in order of impact:

- **Be specific about the output contract.** Format, length, structure, what to do when uncertain.
- **Give examples** rather than describing what you want abstractly (see 1.4).
- **Assign a role and success criteria** — "You are reviewing this for X; flag anything that violates Y."
- **Let the model reason before answering** on multi-step problems.
- **Use structural delimiters** (XML tags, headings) so the model can tell instructions from data. This also matters for injection resistance.
- **Chain prompts** — decompose a hard task into several focused calls instead of one overloaded one.

Prompts are code. Version them, test them, and keep them out of scattered f-strings.

**Go deeper:** [Anthropic prompt engineering documentation](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview) — practical and technique-by-technique.

---

### 1.4 What is few-shot vs zero-shot prompting?

**Zero-shot:** instruction only, no examples. `Classify the sentiment of this review: ...`

**Few-shot:** instruction plus worked examples of input→output before the real input.

```
Input: "Shipping took three weeks."     → negative
Input: "Arrived early, works great."    → positive
Input: "It's fine I guess."             → ?
```

Few-shot is the fix when zero-shot output has the right content but the wrong shape — inconsistent formatting, wrong granularity, edge cases handled inconsistently. Examples communicate a format faster and more reliably than a paragraph describing it.

Costs: examples consume context on every call, and 3–5 well-chosen examples typically capture most of the gain. Include your edge cases, not just the easy ones — the model generalizes from what you show it.

**Go deeper:** [Lil'Log — Prompt Engineering (Lilian Weng)](https://lilianweng.github.io/) — the prompt engineering post covers in-context learning and example selection with the underlying research.

---

### 1.5 What is temperature in LLM generation?

The model outputs a probability distribution over the next token. Temperature rescales that distribution before sampling.

| Temperature | Effect | Use for |
|---|---|---|
| 0 (or near) | Always picks the highest-probability token | Classification, extraction, structured output, anything you need to be reproducible |
| ~0.7 | Moderate diversity | General conversation, drafting |
| >1.0 | Flattens the distribution; low-probability tokens become likely | Brainstorming, creative variation |

Related knobs: **top-p** (nucleus sampling — sample only from the smallest set of tokens whose cumulative probability exceeds p) and **top-k** (sample from the k most likely tokens). Tune one, not all three.

Important: temperature 0 is not a correctness setting. It makes output *consistent*, not *accurate* — a confidently wrong answer will be returned consistently.

**Go deeper:** [How to generate text — Hugging Face](https://huggingface.co/blog/how-to-generate) — walks through greedy, beam, top-k, and nucleus sampling with code and side-by-side output.

---

### 1.6 What is hallucination in LLMs?

Output that is fluent, confident, and false. It isn't a bug in the sense of a broken code path — it's the direct consequence of a system trained to produce plausible continuations rather than to distinguish knowing from not-knowing.

Common shapes: invented citations and URLs, fabricated API methods, wrong numbers stated precisely, and confident answers about things after the training cutoff.

Mitigations, most to least effective:
1. **Ground in retrieved context** and require citations (§2). No source, no claim.
2. **Constrain the task** — extraction from provided text hallucinates far less than open-ended generation.
3. **Verify programmatically** — check that cited sources exist, that generated code compiles, that numbers reconcile.
4. **Give an explicit out** — instruct the model to say it doesn't know, and it will do so more often.
5. **Cross-check with a second call** for high-stakes output.

What does *not* work: asking the model how confident it is and trusting the answer.

**Go deeper:** [Deep Dive into LLMs like ChatGPT](https://www.youtube.com/watch?v=7xTGNNLPyMI) — the hallucination section explains why models hallucinate in terms of the training process, and how tool use and knowledge-based refusal mitigate it.

---

### 1.7 What is instruction tuning?

Supervised fine-tuning on a broad mixture of tasks phrased as instructions, so the model learns to follow instructions in general rather than to complete text.

This is what converts a base model into something you can talk to. Before it, `Summarize this article:` might get you a list of similar article titles — a plausible web-text continuation. After it, you get a summary.

The key finding is generalization: train on enough varied instruction-shaped tasks and the model follows instruction types it never saw during tuning.

**Go deeper:** [Finetuned Language Models Are Zero-Shot Learners (FLAN paper)](https://arxiv.org/abs/2109.01652) — the paper that established instruction tuning as a technique.

---

### 1.8 What is RLHF?

**Reinforcement Learning from Human Feedback.** Instruction tuning teaches the model to answer; RLHF teaches it which of several valid answers people actually prefer.

Pipeline:
1. Generate multiple responses to the same prompt.
2. Humans rank them.
3. Train a **reward model** on those rankings to predict human preference.
4. Optimize the LLM against the reward model with RL (typically PPO), with a penalty for drifting too far from the SFT model.

Why it exists: "helpful, appropriately cautious, well-calibrated in tone" is easy to recognize and nearly impossible to specify as a loss function. RLHF learns the preference instead of requiring you to write it down.

Variants: **RLAIF** replaces human labelers with model-generated preferences to scale; **DPO** skips the separate reward model and optimizes preferences directly, and is simpler and cheaper to run.

Known failure mode: **reward hacking** — the model optimizes the reward model's quirks rather than genuine quality, producing sycophancy or padded, hedge-heavy answers.

**Go deeper:** [Training language models to follow instructions with human feedback (InstructGPT paper)](https://arxiv.org/abs/2203.02155) — the canonical RLHF reference.

---

### 1.9 What are context windows in LLMs?

The maximum number of tokens the model can attend to in a single forward pass — the system prompt, conversation history, retrieved documents, tool schemas, tool results, and the response, all counted together.

Practical consequences:

- **It is a hard limit.** Exceeding it means truncation or an error, and truncation typically drops the oldest content, which is often your instructions.
- **Cost and latency scale with it.** Attention cost grows quadratically with sequence length; a large context is billed on every single call.
- **Advertised length ≠ usable length.** Retrieval accuracy degrades for information buried in the middle of a long context — the "lost in the middle" effect. Put critical instructions at the start or the end.
- **A big window is not a substitute for retrieval.** Dumping an entire corpus in is more expensive and often less accurate than retrieving the right 5 chunks.

Treat context as a budget you actively manage: summarize old turns, retrieve selectively, trim tool output before it lands in the window.

**Go deeper:** [Lost in the Middle: How Language Models Use Long Contexts](https://arxiv.org/abs/2307.03172) — the empirical result behind "long context degrades in the middle."

---

### 1.10 What are embeddings and why are they used with LLMs?

An embedding is a fixed-length vector of floats representing a piece of text, positioned so that semantically similar text lands nearby in the vector space. "How do I reset my password?" and "I forgot my login credentials" share no keywords but sit close together.

This is the mechanism that makes semantic search possible, and semantic search is what makes RAG possible (§2).

What matters in practice:
- **Model choice determines quality.** Embeddings from different models are not interchangeable — you cannot mix them in one index.
- **Changing the embedding model means re-indexing everything.** Budget for this.
- **Dimensionality is a cost/quality tradeoff.** Larger vectors capture more nuance and cost more to store and search.
- **Domain matters.** General-purpose embeddings underperform on dense internal jargon, acronym-heavy documentation, and code.

Beyond retrieval, embeddings are also the basis for clustering, deduplication, classification, and recommendation.

**Go deeper:** [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) — standard benchmark for comparing embedding models across retrieval, classification, and clustering tasks. Check it before picking one.

---

## 2. RAG (Retrieval Augmented Generation)

### 2.1 What is RAG and why is it used?

Retrieval Augmented Generation: retrieve relevant documents at query time, insert them into the prompt, and instruct the model to answer from them.

```
Query → retrieve top-k relevant chunks → build prompt (query + chunks + instructions) → LLM → cited answer
```

Why it's the default architecture for grounded systems:

- **Fresh** — update the index, not the model.
- **Attributable** — the answer can cite the source it came from, which makes it auditable.
- **Access-controllable** — filter retrieval by user permissions.
- **Cheap** — no training run, and iteration is measured in minutes.
- **Correctable** — a wrong answer traces to a specific bad or missing document you can fix.

RAG vs. fine-tuning is not a competition. RAG supplies *knowledge*; fine-tuning shapes *behavior, format, and style*. If the model doesn't know something, use RAG. If it knows but responds in the wrong shape, fine-tune or prompt better.

**Go deeper:** [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks (Lewis et al.)](https://arxiv.org/abs/2005.11401) — the original RAG paper.

---

### 2.2 What problem does RAG solve in LLM systems?

Five concrete problems:

| Problem | How RAG addresses it |
|---|---|
| **Knowledge cutoff** | Retrieval supplies post-cutoff information |
| **No private data** | Your runbooks, tickets, and internal docs were never in the training set |
| **Hallucination** | Grounding in provided text plus enforced citation constrains invention |
| **No attribution** | Every claim points to a retrievable source |
| **Stale knowledge** | Re-index instead of re-train |

The private-data point is usually the one that matters most internally. No amount of model capability substitutes for knowing what your team wrote down last quarter.

**Go deeper:** [Pinecone Learning Center — RAG](https://www.pinecone.io/learn/) — vendor-produced but genuinely the most complete free RAG curriculum available.

---

### 2.3 What are embeddings in RAG pipelines?

Embeddings are the index. The pipeline uses them in two places:

**Indexing (offline):** documents → chunks → embedding model → vectors → vector database, alongside metadata (source, date, permissions, section).

**Query (online):** user query → same embedding model → vector → similarity search → top-k chunks.

Non-negotiable rule: **the query and the documents must be embedded with the same model.** Vectors from different models are not comparable.

Two things that bite teams:
- Some models expect asymmetric prefixes for queries vs. documents. Read your model's docs.
- Embedding quality caps everything downstream. A perfect prompt cannot recover from retrieving the wrong chunk.

**Go deeper:** [Pinecone Learning Center — Core Components](https://www.pinecone.io/learn/category/core-components/)

---

### 2.4 What is a vector database?

A database purpose-built to store high-dimensional vectors and answer "find the k nearest vectors to this one" quickly.

Exact nearest-neighbor search is O(n) — untenable over millions of vectors. Vector databases use **approximate nearest neighbor (ANN)** indexes (HNSW, IVF, product quantization) that trade a small amount of recall for orders-of-magnitude speedup.

Capabilities worth evaluating:
- **Metadata filtering** — restrict to a date range, document type, or permission group. Underrated and usually essential.
- **Hybrid search** — combine vector similarity with keyword/BM25 matching. Critical for exact-match terms like error codes, part numbers, and internal acronyms, where pure semantic search fails.
- **Upserts and deletes** — documents change; the index must keep up.
- **Namespacing / multi-tenancy** — isolating data per team or customer.

**Go deeper:** [What is a Vector Database? — Pinecone](https://www.pinecone.io/learn/) — see the vector database section of the Learning Center.

---

### 2.5 What are popular vector databases?

| Option | Shape | Fits when |
|---|---|---|
| **pgvector** | Postgres extension | You already run Postgres and want one system, not two. Start here more often than teams do. |
| **Chroma** | Embedded / lightweight | Prototyping, local-first, single-machine |
| **Qdrant** | Open-source server, Rust | Self-hosted production with strong filtering |
| **Weaviate** | Open-source server | Hybrid search and built-in module ecosystem |
| **Milvus** | Open-source, distributed | Very large scale, billions of vectors |
| **FAISS** | Library, not a database | You want an index primitive to embed in your own service |
| **Pinecone** | Managed SaaS | You want no operational burden and accept vendor lock-in |
| **Elasticsearch / OpenSearch** | Search engine + vector support | You already run it for logs and want hybrid search cheaply |

Selection guidance: at under ~1M vectors, almost anything works and the differentiator is operational fit, not benchmark performance. Choose based on what your team already runs. Put an adapter interface in front of it so swapping later is a contained change.

**Go deeper:** [Pinecone Learning Center — vector database comparisons](https://www.pinecone.io/learn/)

---

### 2.6 What is chunking in RAG pipelines?

Splitting documents into retrievable segments before embedding. It is the highest-impact and most-neglected decision in a RAG pipeline.

Why it's necessary: embedding models have their own context limits, and a vector representing a 50-page document is too diluted to match any specific query.

The tension: **chunks must be small enough to be precise and large enough to be self-contained.** A chunk that says "This reduces latency by 40%" is useless if "this" is defined two chunks earlier.

Strategies, roughly increasing in sophistication:

| Strategy | How | Good for |
|---|---|---|
| Fixed-size + overlap | N tokens, ~10–20% overlap | Baseline. Start here. |
| Recursive character | Split on paragraph → sentence → word, in order | General prose. Sensible default. |
| Document-structure-aware | Split on headings, sections, code blocks | Technical docs, runbooks, Markdown |
| Semantic | Split where embedding similarity between sentences drops | Unstructured text with topic shifts |
| Parent-document | Retrieve small chunks, return the larger parent for context | Precision retrieval, full context to the LLM |

Always attach metadata (source, section heading, date, permissions) to each chunk. It powers filtering and citation, and it costs nothing at index time.

**Go deeper:** [Chunking Strategies for LLM Applications — Pinecone](https://www.pinecone.io/learn/chunking-strategies/)

---

### 2.7 What is semantic search?

Search by meaning rather than by literal terms. Embed the query, embed the corpus, return the nearest neighbors by cosine similarity.

Versus keyword search (BM25/TF-IDF):

| | Semantic | Keyword |
|---|---|---|
| Matches paraphrases, synonyms | Yes | No |
| Matches exact rare strings (`ERR_0x8004`, part numbers) | Poorly | Yes |
| Handles typos | Somewhat | No |
| Explains why a result matched | No | Yes |
| Needs an embedding model | Yes | No |

Neither dominates, which is why production systems run **hybrid search** — both retrievers, results merged with Reciprocal Rank Fusion or a weighted score. For internal engineering documentation full of error codes, acronyms, and identifiers, hybrid is not optional; pure semantic search will silently miss exact-match queries.

**Go deeper:** [Pinecone Learning Center — semantic and hybrid search](https://www.pinecone.io/learn/)

---

### 2.8 How does retrieval work in RAG?

Full path, with the stages most teams skip marked:

1. **Query preprocessing** *(often skipped)* — rewrite the raw query for retrieval. Expand acronyms, resolve pronouns against conversation history, or generate multiple query variants. A follow-up like "what about the other one?" is useless as a search query until rewritten.
2. **Embed the query** with the same model used for indexing.
3. **Retrieve** — ANN search for top-k, plus BM25 if hybrid, plus metadata filters.
4. **Fuse** — merge result sets if using multiple retrievers.
5. **Rerank** *(often skipped)* — a cross-encoder scores each (query, chunk) pair jointly and reorders. Slower per item but far more accurate than vector similarity. Standard pattern: retrieve 50 cheaply, rerank, keep 5.
6. **Assemble context** — deduplicate, order deliberately (best results at the edges, not buried in the middle — see 1.9), stay within budget.
7. **Generate** with instructions to answer only from provided context and to cite sources.
8. **Post-process** — verify citations resolve to real retrieved chunks.

Steps 1 and 5 are where most of the easy accuracy gains live.

**Go deeper:** [Pinecone Learning Center — retrieval and reranking](https://www.pinecone.io/learn/)

---

### 2.9 How do you improve RAG accuracy?

**Diagnose before optimizing.** Nearly every RAG quality problem is a *retrieval* problem, not a generation problem. Check first: was the correct chunk in the retrieved set? If no, fix retrieval. If yes and the answer is still wrong, fix the prompt or the model.

Measure retrieval separately with recall@k and precision@k against a labeled query set. Without this, you're guessing.

**Retrieval fixes, roughly by impact:**
- **Add a reranker** — usually the single largest gain for the least work.
- **Go hybrid** — add BM25 alongside vector search.
- **Fix chunking** — revisit size, overlap, and structure-awareness (2.6).
- **Contextual retrieval** — prepend a short LLM-generated description of each chunk's place in its parent document before embedding. Anthropic reported large reductions in retrieval failures from this technique.
- **Query rewriting** — expand acronyms, decompose multi-part questions, generate query variants.
- **Better embedding model** — check MTEB; consider a domain-tuned model for jargon-heavy corpora.
- **Metadata filtering** — narrow the search space before searching it.

**Generation fixes:**
- Instruct explicitly: answer only from the provided context; if the context is insufficient, say so.
- Require inline citations to chunk IDs, and verify them programmatically.
- Reorder context so the most relevant material isn't in the middle.

**Data fixes:** garbage in the corpus is the most common root cause. Outdated docs, duplicated content, and badly parsed PDFs and tables all surface as "the model is wrong."

**Go deeper:** [Introducing Contextual Retrieval — Anthropic](https://www.anthropic.com/news/contextual-retrieval) — technique, measured results, and implementation notes. Also see [Ragas](https://docs.ragas.io/) for RAG-specific evaluation metrics.

---

## 3. System Design & Production AI

### 3.1 How would you design a scalable AI system?

Layered, with each layer independently scalable:

```
Client
  → API gateway (auth, rate limit, quota)
    → Orchestration (routing, prompt assembly, tool calls, retries)
      → Retrieval (vector DB, keyword index, cache)
      → Model serving (hosted API and/or self-hosted inference)
        → Storage (documents, traces, feedback, evals)
Observability spans all layers
```

Design principles specific to AI systems:

- **Stateless orchestration.** Keep conversation state in Redis or a database, not in process memory, so you can scale horizontally.
- **Async everywhere.** Model calls take seconds. Blocking threads on them destroys throughput.
- **Cache at multiple levels** — prompt caching for stable prefixes, semantic caching for near-duplicate queries, embedding caching for unchanged documents.
- **Queue long-running work.** Anything past a few seconds becomes a job with a status endpoint, not a synchronous request.
- **Adapter seams around every external dependency.** Model providers, vector stores, and embedding models all change. Isolate them behind interfaces.
- **Degrade gracefully.** Model unavailable → fall back to a smaller model, cached response, or an honest error. Never a silent failure.
- **Budget enforcement in code** — token, cost, and step limits, checked at runtime.

**Go deeper:** [Designing Machine Learning Systems / Chip Huyen's blog](https://huyenchip.com/blog/) — the reference work on ML system design.

---

### 3.2 How do you deploy machine learning models?

Deployment patterns:

| Pattern | Latency | Fits |
|---|---|---|
| **Batch / offline** | Hours | Scoring runs on a schedule, results written to a table |
| **Online (REST/gRPC service)** | ms–s | Per-request inference. The default. |
| **Streaming** | ms | Event-driven scoring off a message bus |
| **Edge / on-device** | ms | Privacy constraints, offline operation, latency floors |

What separates a deployment from a demo:

- **Artifact versioning.** Model weights, preprocessing code, and feature logic are versioned together. A model without its exact preprocessing is not reproducible.
- **Train/serve consistency.** The most common production ML bug is preprocessing that differs between training and serving. Share the code path.
- **Containerize.** Pin dependencies. ML environments break in ways application environments don't.
- **Progressive rollout.** Shadow mode (run in parallel, log, don't serve) → canary → full. Never a cutover.
- **A rollback path that has actually been tested.**
- **Health checks that test inference**, not just process liveness.

**Go deeper:** [ml-ops.org](https://ml-ops.org/) and [MLOps: Continuous delivery and automation pipelines in ML — Google Cloud](https://cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning)

---

### 3.3 What is model monitoring in production?

Tracking whether a deployed model is still doing its job. Distinct from application monitoring: a model degrades silently while every service-health metric stays green.

Four layers, all needed:

| Layer | Metrics | Detects |
|---|---|---|
| **Operational** | Latency (p50/p95/p99), throughput, error rate, cost/request | Infrastructure problems |
| **Data** | Missing values, schema changes, range violations, null rates | Broken upstream pipelines — the most common real cause of "the model broke" |
| **Drift** | Input distribution shift, prediction distribution shift | Changing conditions (3.4) |
| **Quality** | Accuracy, precision/recall, business KPIs | Actual degradation |

The hard part is that ground-truth labels arrive late or never. Proxies: prediction drift, user corrections and overrides, downstream conversion, thumbs-up/down, escalation rate.

**For LLM systems, add:** token usage per request, tool-call success rate, retrieval hit rate, refusal rate, hallucination rate via LLM-as-judge on a sample, and full trace capture for individual runs.

**Go deeper:** [Evidently AI — ML monitoring guides](https://www.evidentlyai.com/ml-in-production/data-drift) — practical, tool-agnostic, and the best free material on this topic.

---

### 3.4 What is model drift and data drift?

Three distinct phenomena that get conflated:

| Type | Formal | Plain | Example |
|---|---|---|---|
| **Data drift** (covariate shift) | P(X) changes | Inputs look different | A feature's range shifts after an upstream unit change |
| **Concept drift** | P(Y\|X) changes | The relationship changed | Behavior that predicted churn last year no longer does |
| **Target/label drift** | P(Y) changes | Output distribution shifted | Fraud rate moves from 2% to 8% |

"Model drift" is the umbrella term for the resulting performance decay. The model itself doesn't change — the world does.

**Detection:** compare a reference window against a current window using KS tests, PSI, Jensen-Shannon distance, or Wasserstein distance. For text and embeddings, a domain classifier works better than per-feature distribution tests: train a binary classifier to distinguish reference from current data, and a high ROC AUC means the distributions have separated.

**Response:** alert → investigate root cause → decide. Retrain on recent data if the world genuinely changed; fix the pipeline if the drift is a data bug. Automatic retraining on every drift alert will happily train your model on corrupted input.

Note that drift is often a **data quality bug, not a real-world change**. Check that first.

**Go deeper:** [What is data drift in ML, and how to detect and handle it — Evidently AI](https://www.evidentlyai.com/ml-in-production/data-drift)

---

### 3.5 How do you handle large scale inference?

**Reduce work per request:**
- **Quantization** — INT8/FP8/4-bit weights. Large memory and throughput wins for modest quality loss.
- **Distillation** — train a small model on a large model's outputs.
- **Right-size the model.** Most steps in a pipeline don't need the frontier model.

**Serve more efficiently:**
- **Continuous batching** — the biggest throughput lever for LLM serving. Insert new requests into the batch as others finish instead of waiting for the whole batch.
- **KV cache management** (e.g. PagedAttention) — memory is the binding constraint in LLM serving, not compute.
- **Model parallelism** for models exceeding single-GPU memory.

**Avoid work entirely:**
- Prompt caching for repeated prefixes (system prompts, few-shot examples, long documents).
- Semantic caching for near-duplicate queries.
- Precompute embeddings; never re-embed unchanged documents.

**Scale out:**
- Queue-based architecture with autoscaling workers.
- Route by complexity — cheap model first, escalate on low confidence.
- Batch API tiers for non-interactive work, usually at a steep discount.

**Go deeper:** [vLLM documentation](https://docs.vllm.ai/) — continuous batching and PagedAttention explained by the project that popularized both. Also [Lil'Log — Large Transformer Model Inference Optimization](https://lilianweng.github.io/).

---

### 3.6 What is model versioning?

Treating models as versioned, reproducible artifacts rather than files someone copied to a server.

A version is not just weights. To reproduce a prediction you need: weights, training data snapshot, preprocessing code, hyperparameters, evaluation results, dependency versions, and training code commit. Version them as a unit.

Why it matters: you cannot roll back what you cannot reproduce, you cannot audit a decision without knowing which model made it, and you cannot compare two models fairly without knowing what differed.

Practices:
- **Model registry** (MLflow, or your artifact store) with lifecycle stages: staging → production → archived.
- **Semantic-ish versioning** — major for architecture or interface change, minor for retraining on new data.
- **Log the model version with every prediction.** Non-negotiable for debugging.
- **Immutable artifacts.** Never overwrite a version in place.

**For LLM systems:** the equivalent is a **prompt registry**. Prompts are the thing you change most often and are equally capable of silently breaking production. Version them, test them, and log which version produced each output.

**Go deeper:** [MLflow](https://mlflow.org/) — model registry and experiment tracking, the de facto standard.

---

### 3.7 What are A/B tests for ML models?

Splitting live traffic between model variants to measure real-world impact, because offline metrics routinely fail to predict online outcomes.

Deployment strategies in escalating order of risk:

| Strategy | Mechanism | Purpose |
|---|---|---|
| **Shadow** | New model runs on real traffic; output logged, not served | Validate correctness and latency at zero user risk |
| **Canary** | Small traffic slice (1–5%) served by the new model | Catch failures with bounded blast radius |
| **A/B test** | Randomized split, statistically powered | Measure the actual effect |
| **Interleaving** | Both models' results merged in one response | Ranking and search; needs far less traffic |
| **Multi-armed bandit** | Traffic shifts adaptively toward the winner | Continuous optimization; reduced regret |

Getting it right:
- **Define the metric before launching.** Business outcome, not model accuracy.
- **Randomize by user, not by request** — otherwise one user sees both variants and the experience is incoherent.
- **Compute the sample size in advance** and don't peek-and-stop; that inflates false positives.
- **Track guardrail metrics** (latency, cost, error rate), not just the target metric.

**For LLM systems:** the same machinery applies to prompt versions, retrieval configurations, and model choices — often with an LLM-as-judge or user thumbs-up rate as the measured outcome.

**Go deeper:** [Eugene Yan's writing on ML systems](https://eugeneyan.com/writing/) — consistently strong, practitioner-level treatment of experimentation and evaluation.

---

### 3.8 How do you optimize latency in AI systems?

**Measure first.** Instrument every stage — retrieval, prompt assembly, model call, post-processing — and find where the time actually goes. It is frequently not where you assume.

Then, roughly by impact:

1. **Stream the response.** Doesn't reduce total time; dramatically reduces *perceived* latency. Usually the highest-value change for interactive systems.
2. **Parallelize independent work.** Retrieval, multiple tool calls, and independent sub-agent tasks should not be sequential.
3. **Right-size the model.** Smaller models are several times faster. Reserve the large model for the steps that need it.
4. **Trim input context.** Fewer input tokens means faster time-to-first-token.
5. **Constrain output length.** Output tokens are generated serially — this is often the dominant term in total latency.
6. **Cache.** Prompt caching for stable prefixes, semantic caching for repeat queries.
7. **Speculative decoding** — a small model drafts, the large model verifies.
8. **Faster providers or self-hosting** — measure, don't assume.

Set explicit latency budgets per stage, and monitor p95/p99 rather than the mean. The mean hides the experience that generates complaints.

**Go deeper:** [Lil'Log — Large Transformer Model Inference Optimization](https://lilianweng.github.io/) — the technical grounding on where inference time actually goes.

---

### 3.9 How would you build a real-time AI service?

Requirements first: what does "real-time" mean here — 100ms, 1s, or 10s? The answer determines the entire architecture.

Reference shape:

```
Request → gateway (auth, rate limit)
  → async orchestrator
     ├→ cache check (semantic + exact)         [fast path, return immediately]
     ├→ parallel retrieval (vector + keyword)
     └→ model call (streaming)
  → stream tokens to client via SSE/WebSocket
  → async: log trace, update cache, capture feedback
```

Design decisions:
- **Streaming transport** (SSE or WebSocket) so the user sees output immediately.
- **Cache before compute.** A cache hit is the fastest possible response.
- **Timeouts at every hop**, with a defined fallback for each.
- **Circuit breakers** on external dependencies. A degraded provider should fail fast, not consume your entire connection pool.
- **Move everything non-essential off the request path** — logging, analytics, index updates all go async.
- **Backpressure.** Under overload, shed load deliberately with clear errors rather than queueing until everything times out.

**Go deeper:** [Real-time machine learning: challenges and solutions — Chip Huyen](https://huyenchip.com/blog/)

---

### 3.10 How do you ensure reliability of AI systems in production?

AI systems fail differently from ordinary software: they fail *plausibly*. A wrong answer returns HTTP 200 with a confident tone. Reliability engineering has to account for that.

**Correctness controls:**
- **Validate every output** against a schema before it reaches a user or a downstream system.
- **Guardrails** — deterministic checks first, LLM checkers where judgment is required, human approval on consequential or irreversible actions.
- **Ground and cite** — no source, no claim.
- **Confidence thresholds with escalation** — low-confidence cases route to a stronger model or to a human.

**Availability controls:**
- Retries with exponential backoff and jitter.
- Fallback chains: primary model → secondary provider → smaller model → cached response → honest error.
- Circuit breakers and timeouts on every external call.
- Rate limiting and quotas to prevent one caller from exhausting shared capacity.

**Operational controls:**
- **Full trace logging** — every prompt, tool call, retrieval result, and decision point, sufficient to reproduce any run.
- **Continuous evaluation** — a regression suite that runs on every prompt or model change. This is the single practice that most distinguishes reliable LLM systems from unreliable ones.
- **Incremental rollout with a tested rollback.**
- **Feedback capture** wired into the eval set, so production failures become test cases.

**Security** is part of reliability: treat all retrieved and tool-returned content as untrusted input, sandbox code execution, scope credentials per component, and enforce hard budgets on tokens, steps, and wall-clock time.

**Go deeper:** [Google SRE Book](https://sre.google/books/) for reliability fundamentals, and [Building effective agents — Anthropic](https://www.anthropic.com/engineering/building-effective-agents) for the LLM-specific patterns.

---

## 4. ML & Deep Learning Fundamentals

### 4.1 What is the difference between supervised, unsupervised, and reinforcement learning?

| | Supervised | Unsupervised | Reinforcement |
|---|---|---|---|
| **Input** | Labeled examples (X, y) | Unlabeled data (X) | Environment + reward signal |
| **Goal** | Predict y from X | Find structure in X | Learn a policy maximizing cumulative reward |
| **Feedback** | Correct answer, immediately | None | Delayed, sparse reward |
| **Examples** | Classification, regression | Clustering, dimensionality reduction, anomaly detection | Game playing, robotics, RLHF |
| **Main cost** | Labeling | Validating that the structure found is meaningful | Sample efficiency; reward specification |

**Self-supervised learning** is the fourth category and the one that matters most for LLMs: labels are generated automatically from the data's own structure. Next-token prediction is self-supervised — the label for each position is simply the next token in the text. This is what makes training on the entire web possible without human annotation.

An LLM touches three of these: self-supervised pre-training, supervised fine-tuning, and reinforcement learning from preferences (§1.2).

**Go deeper:** [Google Machine Learning Crash Course](https://developers.google.com/machine-learning/crash-course) — free, well-paced, with interactive exercises.

---

### 4.2 What are overfitting and underfitting, and how do you prevent them?

**Overfitting:** the model memorizes the training set, including its noise. Training error low, validation error high, and the gap widens with training.

**Underfitting:** the model is too simple to capture the signal. Both training and validation error are high.

Diagnose by comparing the two curves:

| Training error | Validation error | Diagnosis |
|---|---|---|
| High | High | Underfitting |
| Low | High | Overfitting |
| Low | Low | Working |
| High | Low | Bug — usually a data leak or a mismatched split |

**Fixing overfitting:** more training data (most effective); data augmentation; regularization (L1/L2, dropout, weight decay); early stopping on validation loss; reduce model capacity; ensembling.

**Fixing underfitting:** increase capacity; better features; train longer; reduce regularization; check that the features actually contain the signal.

The subtle version: **overfitting to the validation set.** If you tune hyperparameters against validation performance hundreds of times, you have fit the validation set. That's what the test set is for (4.4).

**Go deeper:** [Google Machine Learning Crash Course — Generalization and Regularization](https://developers.google.com/machine-learning/crash-course)

---

### 4.3 What is the bias vs variance tradeoff?

Expected prediction error decomposes into three parts:

**Error = Bias² + Variance + Irreducible noise**

- **Bias** — error from wrong assumptions. A high-bias model is too simple and misses real structure. Underfits.
- **Variance** — error from sensitivity to the particular training sample. A high-variance model changes a lot if you resample the data. Overfits.
- **Irreducible noise** — inherent randomness. No model removes this, and pursuing it is how you overfit.

Classically these trade off: increasing model complexity lowers bias and raises variance, so there is an optimum in between.

| High bias | High variance |
|---|---|
| Linear model on nonlinear data | Deep tree with no pruning |
| Heavy regularization | Small training set, large model |
| Fix: more capacity, better features | Fix: more data, regularization, ensembling |

**The modern caveat worth knowing:** very large overparameterized networks exhibit **double descent** — past the interpolation threshold, test error decreases again as capacity grows. The classical U-shaped curve is a good mental model for small and mid-sized models but does not fully describe deep networks at scale.

**Go deeper:** [StatQuest — Bias and Variance](https://www.youtube.com/@statquest) — the clearest short explanation of this concept available.

---

### 4.4 What are training, validation, and test datasets?

| Split | Used for | Seen by the model | How often |
|---|---|---|---|
| **Training** | Fitting parameters | Yes, directly | Every epoch |
| **Validation** | Tuning hyperparameters, early stopping, model selection | Indirectly, through your decisions | Many times |
| **Test** | Final unbiased performance estimate | Never, until the end | Once |

The three-way split exists because tuning against validation performance leaks information into the model through your choices. The test set is the only remaining honest estimate — and it stops being honest the moment you use it to make a decision.

Splitting correctly matters more than the ratio:

- **Random splits are wrong for time-series data.** Split chronologically or you leak the future into training.
- **Group-aware splitting** — all records from the same user, patient, or device belong to one split. Otherwise you leak.
- **Stratify** on the target for imbalanced classes.
- **Split before preprocessing.** Fitting a scaler or imputer on the full dataset leaks test statistics into training. This is the most common leak in practice.

**Cross-validation** (k-fold) gives a more reliable estimate on small datasets by rotating the validation fold, at k× the training cost.

**For LLM systems** the analogue is your eval set: a held-out set of prompts with known-good outputs, never used for prompt iteration, run on every change.

**Go deeper:** [scikit-learn — Cross-validation: evaluating estimator performance](https://scikit-learn.org/stable/modules/cross_validation.html)

---

### 4.5 What is gradient descent and its variants?

An optimization algorithm: compute the gradient of the loss with respect to the parameters, then step in the opposite direction.

```
θ ← θ − η · ∇L(θ)        η = learning rate
```

The gradient points uphill in loss; the negative gradient points toward the steepest decrease. Repeat until convergence.

**Batch-size variants:**

| Variant | Gradient computed on | Trade-off |
|---|---|---|
| Batch GD | Entire dataset | Stable, accurate, intractable at scale |
| Stochastic GD (SGD) | One example | Fast, very noisy |
| Mini-batch SGD | 32–512 examples | The practical default; the noise even helps escape sharp minima |

**Adaptive optimizers:**

| Optimizer | Adds |
|---|---|
| **Momentum** | Accumulates a velocity term — accelerates along consistent directions, damps oscillation |
| **RMSProp** | Per-parameter learning rate scaled by recent gradient magnitude |
| **Adam** | Momentum + RMSProp. The default for most deep learning. |
| **AdamW** | Adam with decoupled weight decay. The standard for training Transformers. |

**Learning rate is the hyperparameter that matters most.** Too high and training diverges; too low and it crawls or stalls in a bad region. Standard practice is a warmup followed by cosine or linear decay.

**Go deeper:** [Gradient descent, how neural networks learn — 3Blue1Brown](https://www.3blue1brown.com/lessons/gradient-descent/) — visual and genuinely clarifying. For momentum specifically, [Why Momentum Really Works — Distill](https://distill.pub/2017/momentum/).

---

### 4.6 What is backpropagation and how does it work?

The algorithm that computes the gradient of the loss with respect to every parameter in a network, efficiently. Gradient descent decides *how to step*; backpropagation computes *what the gradient is*.

**How it works:** a neural network is a composition of functions. Backpropagation applies the chain rule from the output backward, computing at each layer how sensitive the loss is to that layer's parameters, and reusing already-computed downstream derivatives instead of recomputing them.

**Two passes per training step:**
1. **Forward** — input flows through the layers producing a prediction; intermediate activations are cached.
2. **Backward** — the loss gradient propagates from output to input, producing a gradient for every weight and bias along the way.

**Why it's efficient:** computing each of millions of partial derivatives independently would be intractable. Backpropagation gets all of them in roughly the cost of one forward pass, by sharing intermediate results across the chain. That efficiency is the reason deep learning is possible at all.

**What matters in practice:**
- Gradients can **vanish** (shrink toward zero through many layers, so early layers stop learning) or **explode** (grow without bound, destabilizing training). Residual connections, normalization layers, careful initialization, and gradient clipping are the standard mitigations.
- The cached activations are why training uses far more memory than inference — the entire forward pass must be retained for the backward pass.

**Go deeper:** [What is backpropagation really doing? — 3Blue1Brown](https://www.3blue1brown.com/topics/neural-networks), followed by [Backpropagation calculus](https://www.3blue1brown.com/lessons/backpropagation-calculus/) for the formal version.

---

## 5. Core Reading List

If someone reads only a handful of these, make it these.

**Foundations**
- [3Blue1Brown — Neural Networks](https://www.3blue1brown.com/topics/neural-networks) — visual intuition for networks, gradient descent, backprop, and attention.
- [Google Machine Learning Crash Course](https://developers.google.com/machine-learning/crash-course) — free, structured, hands-on.
- [The Illustrated Transformer — Jay Alammar](https://jalammar.github.io/illustrated-transformer/) — the standard explanation of the architecture underneath every LLM.
- [Attention Is All You Need](https://arxiv.org/abs/1706.03762) — the original Transformer paper.

**LLMs**
- [Deep Dive into LLMs like ChatGPT — Karpathy](https://www.youtube.com/watch?v=7xTGNNLPyMI) — the best single resource on this list.
- [Hugging Face NLP Course](https://huggingface.co/learn/nlp-course) — hands-on, code-first.
- [Anthropic prompt engineering docs](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview)

**RAG**
- [Pinecone Learning Center](https://www.pinecone.io/learn/) — the most complete free RAG curriculum.
- [Introducing Contextual Retrieval — Anthropic](https://www.anthropic.com/news/contextual-retrieval)
- [Ragas](https://docs.ragas.io/) — RAG evaluation metrics.

**Agents**
- [Building effective agents — Anthropic](https://www.anthropic.com/engineering/building-effective-agents) — simple composable patterns over frameworks.
- [LLM Powered Autonomous Agents — Lilian Weng](https://lilianweng.github.io/posts/2023-06-23-agent/) — the standard conceptual reference.

**Production**
- [Chip Huyen's blog](https://huyenchip.com/blog/) — ML system design.
- [Evidently AI — ML in production guides](https://www.evidentlyai.com/ml-in-production/data-drift) — monitoring and drift.
- [Google — Rules of Machine Learning](https://developers.google.com/machine-learning/guides/rules-of-ml) — 43 hard-won practical rules. Read this before your first production model.
- [ml-ops.org](https://ml-ops.org/) — MLOps principles and tooling landscape.
- [Google SRE Book](https://sre.google/books/) — reliability fundamentals.
- [Eugene Yan](https://eugeneyan.com/writing/) — applied ML systems and evaluation.