---
title: Agentic AI — Reference Notes
description: Reference notes on agentic AI design patterns, autonomy levels, context engineering, and task decomposition, distilled from an external video course for internal use.
tags: [ai-strategy, llm, reference]
status: draft
visibility: internal
owner: ah
updated: 2026-08-01
reviewCycleMonths: 6
order: 50
related: []
---

Source: *AI Agents in 38 Minutes — Complete Course from Beginner to Pro* (YouTube).
Scope: design patterns, quality/cost/latency levers, observability, and security for LLM agent systems.

<div class="video-embed">
  <iframe
    src="https://www.youtube-nocookie.com/embed/sNvuH-iTi4c"
    title="AI Agents in 38 Minutes — Complete Course from Beginner to Pro"
    loading="lazy"
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
    referrerpolicy="strict-origin-when-cross-origin"
    allowfullscreen
  ></iframe>
</div>

---

## 1. Core Concepts

An agent decomposes a task into a workflow and executes it with some degree of independence. Three things determine whether it works: **how much autonomy you grant**, **what context it sees**, and **how the task is split up**.

### 1.1 Degrees of Autonomy

Autonomy is a dial, not a switch. Pick the lowest level that solves the problem — every step up adds failure modes and observability cost.

| Level | Who decides the steps | Who decides the tools | Typical use |
|---|---|---|---|
| Fixed workflow | You | You | Deterministic pipelines, known inputs |
| Router | You (branches) | You | Classify-then-dispatch |
| Tool-calling agent | Model, per step | You (fixed set) | Q&A over tools/APIs |
| Planning agent | Model | Model, from a toolkit | Open-ended tasks |
| Multi-agent | Manager agent | Per-agent scoped sets | Long or parallelizable work |

### 1.2 Context Engineering

Everything the model sees at inference time is context, and all of it is engineered:

- **System prompt** — role, constraints, output contract, refusal conditions.
- **Instructions** — the specific task for this run.
- **Memory** — state carried across steps or runs (see §3).
- **Knowledge** — retrieved reference material (RAG, docs, schemas).
- **Tools** — the schemas and descriptions themselves consume context and shape behavior.
- **History** — prior turns, tool results, intermediate artifacts.

Context is a budget. Trimming it improves latency, cost, and accuracy simultaneously — long contexts degrade retrieval of relevant facts.

### 1.3 Task Decomposition

Start with how *you* would do the task manually, then formalize those steps. Four patterns:

| Pattern | Split by | Use when |
|---|---|---|
| Functional | Role or domain | Distinct skills needed (research vs. write vs. review) |
| Spatial | File or directory structure | Codebases, document trees |
| Temporal | Sequential dependent stages | Each stage needs the prior stage's output |
| Data-driven | Data partitions | Large datasets, map-reduce shaped work |

---

## 2. Design Patterns

### 2.1 Reflection

The agent critiques and revises its own output before returning it. Most effective when the output has a checkable structure — JSON schema conformance, code that must compile, a report that must cover N required sections.

Loop: generate → critique against explicit criteria → revise → stop on pass or max iterations.

Cap the iterations. Reflection without a stopping condition burns tokens on diminishing returns.

### 2.2 Tool Use

Tools give the agent external information and side effects: web search, calendar access, SQL, file I/O.

**A tool has two halves.**

*Interface (what the agent sees):*
- Name
- Plain-English description of **when to use it** — this is the actual routing signal, not the name
- Typed input schema

*Implementation (what the agent doesn't see):*
- Query logic, auth, retries, throttling, response parsing

**Properties of a good tool:**
- Error handling and self-recovery — return an actionable error string, not a stack trace. `"Date must be YYYY-MM-DD, got '03/15'"` lets the agent fix itself; `"ValueError"` does not.
- Rate limiting and backoff.
- Caching for identical inputs — cuts cost, latency, and external API load.
- Async support so the agent (or sibling agents) can keep working.
- Deterministic, bounded output — truncate large payloads before they hit context.

**Treat tools as products:** versioning, documentation, and tests. Maintain an internal registry of vetted tools with docs, versions, and owners so tools are reused rather than reimplemented per agent.

### 2.3 Planning

Instead of hardcoding workflow steps, hand the agent a toolkit and let it determine the sequence.

**Planning loop:**
1. Give the agent access to the tools.
2. Prompt it to produce a plan — an explicit step-by-step list of actions.
3. Execute the plan step by step.
4. Re-plan against results; repeat until done or budget exhausted.

Emit the plan as structured JSON, or have the agent write code that encodes the plan. Either way the plan becomes an inspectable artifact you can log, diff, and evaluate independently of the execution.

Always bound the loop — max steps, max tokens, max wall-clock.

### 2.4 Multi-Agent Collaboration

Each agent gets a clear role (researcher, designer, writer) and a scoped toolset.

**Why:**
- Keeps each agent's context window small and relevant
- Lets you mix models — cheap models for mechanical subtasks, expensive ones for reasoning
- Parallelizes naturally
- Splits long operations into recoverable units

**Topologies:**

| Pattern | Shape | Use when |
|---|---|---|
| Sequential | A → B → C | Each stage depends on the prior one |
| Parallel | A, B, C → merge | Independent subtasks |
| Hierarchical | Manager → sub-agents | Complex tasks needing delegation and synthesis |
| All-to-all | Everyone sees everyone | Brainstorming, adversarial review |

**Failure modes:** redundant work across agents; unnecessary back-and-forth chatter that inflates cost without improving output; context drift as information passes through hand-offs.

**Practices:**
- Define **interfaces, not vibes** — typed hand-off contracts between agents.
- Scope tools per agent; don't give everyone everything.
- Log the trace, keeping per-step artifacts. This is the difference between debuggable and not.
- Evaluate both components and end-to-end.

---

## 3. Memory

| | Memory | Knowledge |
|---|---|---|
| Nature | Dynamic, updated each run | Static reference material |
| Source | The agent's own experience | Curated corpus |
| Example | "Tool X times out on batches >50" | API documentation |

- **Short-term memory** — within or across a session: what worked, what failed, what to change next time.
- **Long-term memory** — distilled lessons, promoted deliberately, reusable to bootstrap other agents.

Not everything should be written to memory. Define what gets promoted from short-term to long-term, or memory becomes an unreviewed accumulation of noise that degrades the context it was meant to improve.

---

## 4. Evaluation

Evaluation is the load-bearing discipline. Build something quickly, then iterate against measurements.

**Layers:**
- **Deterministic checks** — schema validity, required fields present, output length, latency, tool-call correctness. Cheap; run on every output.
- **LLM-as-judge** — a second model scores output against an explicit rubric. Use for subjective quality where deterministic checks can't reach.
- **Human review** — sampled, for calibrating the judge and catching what the rubric missed.
- **End-to-end** — did the run achieve the user's actual goal, not just produce well-formed output.

Evaluate components *and* the full system. A pipeline of individually passing steps can still fail end-to-end.

---

## 5. Guardrails

A guardrail is a **quality gate between what the agent said it did and what it was supposed to do**. Enforcement mechanisms:

- **Code** — deterministic validation, allowlists, schema enforcement, hard limits. Prefer this wherever the rule is expressible.
- **LLM** — a checker model for rules that require judgment.
- **Human in the loop** — approval gating on consequential or irreversible actions.

Guardrails run on inputs (before the agent acts) and outputs (before results are returned or committed).

---

## 6. Improving Quality

### Non-LLM components (search, RAG retrieval)

- **Tune the knobs** — web search date ranges, top-k, chunk size and overlap, similarity thresholds, reranking.
- **Swap providers** — retrieval and search backends vary widely on the same query.

Retrieval quality caps generation quality. Fix retrieval before touching prompts.

### LLM components

- Improve the prompt — clearer contract, explicit criteria, few-shot examples.
- Try another model.
- Decompose hard tasks into smaller ones.
- Fine-tune — last resort, after prompting and decomposition are exhausted.

---

## 7. Latency

1. **Get a baseline** — measure per-step, not just end-to-end.
2. **Parallelize** anything without a dependency.
3. **Right-size the model** — most steps don't need the frontier model.
4. **Try faster providers.**
5. **Trim context** — fewer input tokens, faster time-to-first-token.

---

## 8. Cost

**Where cost comes from:**

| Bucket | Driver |
|---|---|
| LLM calls | Input and output tokens; **output tokens are the expensive side** |
| API calls | Web search, PDF conversion, image generation, speech-to-text — usually per-call or per-unit |
| Infrastructure | Self-hosted retrieval, vector DB, compute for code execution |

**Levers:**
- **Attack the big buckets first** — measure before optimizing.
- **Tier your models** — cheap model for classification and extraction, expensive model for reasoning.
- **Cache aggressively** — prompt caching for stable prefixes, result caching for identical tool inputs.
- **Constrain outputs** — the largest single lever, since output tokens dominate. Ask for the JSON, not the JSON plus an explanation.
- **Batch** where latency is not user-facing.

---

## 9. Monitoring and Observability

Covers debugging, quality monitoring, and hallucination tracking. Two altitudes:

**Zoom-in (single run).** The full trace: prompts, tool calls, token usage, retries, and every decision point — everything required to reproduce an error and see exactly where it went wrong.

**Zoom-out (across many runs).** Automated quality checks (often LLM-as-judge), hallucination rates, success and ROI measures, and trend lines showing whether changes are helping or hurting.

**User behavior analysis.** What are people actually using? Where do they get stuck? Abandonment points identify which parts of the system are failing in practice, independent of your own metrics.

---

## 10. Security

| Threat | Mitigation |
|---|---|
| Prompt injection | Treat all retrieved/tool content as untrusted; separate instructions from data; validate actions against an allowlist rather than trusting model intent |
| Unsafe code generation | Sandbox execution, no host access |
| Data leakage | Scope credentials per agent; redact before logging; classify what may enter context |
| Resource exhaustion | Token, step, and wall-clock budgets per run |
| Infinite loops | Max iterations, loop detection, termination conditions on every agentic loop |

**Safe code execution:**
- Sandbox execution (container, no network unless explicitly granted)
- Resource limits — CPU, memory, timeout
- Allowlisted libraries only
- Validation plus reflection loop before execution
- Deterministic I/O — fixed input and output contracts
- I/O sanitization on both ends

---

## Further Reading

- The Agentic Systems series