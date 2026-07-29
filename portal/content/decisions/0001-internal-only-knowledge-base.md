---
title: Why This Knowledge Base Is Internal-Only
description: The reasoning behind building a separate internal knowledge base rather than extending the public marketing site, and what belongs in each.
tags: [decision, process, tooling]
status: published
visibility: internal
owner: ah
updated: 2026-07-28
reviewCycleMonths: 24
order: 10
---

# Why This Knowledge Base Is Internal-Only

## Status

Accepted.

## Context

The portal was originally scoped as a hybrid: a public marketing surface plus a
knowledge base plus a machine-readable corpus for external LLM crawlers. Three
audiences, one content tree.

That framing produced real architectural consequences. Every page carried an
`audience: public | client | internal` field that gated whether it built at all.
Drafts were excluded from the build. The IA led with Services and About. Build
artifacts included `llms.txt`, a sitemap, JSON-LD, and OpenGraph tags — all
conventions that exist so external crawlers can discover and rank a site.

On review, the hybrid framing was wrong. The thing we actually need is a place
for the team to write down how we work, so that knowledge survives past the
person who holds it.

## Decision

Split the two surfaces.

- The **marketing site** lives in `website/` and targets prospects.
- This **knowledge base** lives in `portal/` and targets the team.

Content that is genuinely dual-purpose gets written here first and marked
`visibility: shareable`. Publishing it externally is then a deliberate copy
step, not an accident of a build flag.

## Consequences

**What got simpler.** The `audience` build gate is gone — everything here is
internal, so there is nothing to gate. Section index pages are generated from
the folder tree rather than hand-written, because the team already knows what
"Runbooks" means; the hand-written overviews only existed to give an external
crawler prose to retrieve.

**What got stricter.** Drafts now render with a banner instead of being hidden.
Hiding work in progress from your own team defeats the purpose of a shared
knowledge base. Ownership is enforced at build time, and every page carries a
`reviewCycleMonths` that drives a staleness warning — internal docs rot silently
because no external pressure exists to keep them current.

**What we kept.** The content contract, computed navigation, and `/index.json`
survived unchanged. The index is arguably more valuable now: it is the ingestion
surface for our own RAG and agent tooling, and it exposes `status` and `isStale`
so a pipeline can down-rank content we already know is unreliable.

**What we gave up.** No SEO, no social cards, no external discoverability. All
intentional. If a page here should reach the outside world, it belongs in
`website/`.
