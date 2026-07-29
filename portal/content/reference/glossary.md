---
title: Glossary
description: Definitions of key terms used across BenchmarkTech's methodology, playbooks, and client deliverables — AI, data, and consulting vocabulary standardized for consistent use.
tags: [reference, ai-strategy, rag, llm, data-engineering]
status: published
visibility: shareable
owner: ah
updated: 2026-07-28
reviewCycleMonths: 12
order: 10
---

# Glossary

Definitions used consistently across all BenchmarkTech materials. When a term appears in a deliverable or playbook, it means what is written here — nothing assumed.

## A

**AI Readiness**
The organizational state in which data infrastructure, workflows, stakeholder alignment, and internal capability are sufficient to successfully deploy and operate a specific AI system. Readiness is use-case-specific — an organization may be ready for document Q&A but not for automated decision-making.

**Acceptance Criteria**
The explicit, testable conditions that define when a deliverable is complete. Acceptance criteria are set during scoping and agreed to in writing before work begins. Vague criteria ("it should work well") are renegotiated before sign-off.

## C

**Chunk**
A unit of text extracted from a document for storage in a vector database. Chunking strategy (size, overlap, boundary detection) is one of the primary levers in RAG pipeline quality. See also: *Retrieval-Augmented Generation*.

**Context Window**
The maximum amount of text a language model can process in a single prompt-plus-completion. Relevant to RAG system design because retrieved chunks must fit within the context window alongside the query and any instructions.

## D

**Discovery Phase**
The structured phase at the start of a build engagement in which requirements are surfaced, constraints identified, and the solution approach confirmed before architecture decisions are made. See [Stakeholder Interview Playbook](/playbooks/discovery/stakeholder-interviews).

## E

**Embedding**
A numerical vector representation of text that captures semantic meaning. Documents and queries are both converted to embeddings for similarity search in a vector database. The embedding model is a significant quality variable in RAG systems.

**Engagement Model**
BenchmarkTech's framework for how consulting engagements are structured and managed from scoping through handoff. See [Engagement Model](/methodology/engagement-model).

## G

**Gap Analysis**
A structured finding document produced during an AI Readiness Assessment. It identifies the difference between the current organizational state and the state required for successful AI deployment, with severity ratings and recommended remediation steps.

## H

**Hallucination**
A language model generating confident, fluent output that is factually incorrect. In RAG systems, hallucination risk is reduced by grounding model responses in retrieved source documents — but not eliminated. Evaluation plans must include hallucination testing.

## L

**LLM (Large Language Model)**
A machine learning model trained on large text corpora, capable of generating, summarizing, classifying, and reasoning over text. GPT-4, Claude, and Gemini are examples. LLMs are a component in AI systems, not the system itself.

## R

**RAG (Retrieval-Augmented Generation)**
An architecture pattern in which a language model's responses are grounded in documents retrieved from an external knowledge base at query time. RAG reduces hallucination and allows models to answer questions about private or recently updated information. The primary architecture pattern BenchmarkTech implements.

**Runbook**
Operational documentation describing how to perform a specific task or respond to a specific failure. Every system BenchmarkTech delivers includes runbooks as part of the handoff package.

## S

**Semantic Search**
Search that finds documents by meaning similarity rather than keyword matching. Built on embedding models and vector databases. The retrieval mechanism in most RAG systems.

**Scope**
The agreed boundary of what an engagement will and will not produce. Scope is defined in writing during the scoping phase. Changes to scope require documented evaluation and agreement before work proceeds. See [Engagement Model](/methodology/engagement-model).

## V

**Vector Database**
A database optimized for storing and querying embedding vectors. Used in RAG systems to store chunked document embeddings and retrieve the most semantically similar chunks for a given query. Examples: Pinecone, Weaviate, pgvector (PostgreSQL extension), Chroma.
