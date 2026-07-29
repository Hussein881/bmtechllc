# BenchmarkTech Knowledge Base

Internal documentation for the team: methodology, playbooks, runbooks, decisions,
and engagement history. Markdown-first — **adding a topic never requires an
application change.**

Not a public site. See [`website/`](../website) for anything prospect-facing.

## Quick start

```bash
npm install
npm run dev      # http://localhost:4321/bmtechllc/portal/
npm run build    # builds + runs all CI gates
```

## Adding a page

Create a Markdown file under the section it belongs to. The folder path becomes
the URL and the navigation position — there is no nav config to update.

```
content/
├── onboarding/    the path a new person walks, in order
├── methodology/   how we work and why
├── playbooks/     how to execute a phase of an engagement
├── runbooks/      operational procedures and incident response
├── reference/     lookups: glossary, standards, checklists
├── templates/     artifacts you copy from at the start of work
├── decisions/     ADRs, so we stop relitigating settled questions
└── engagements/   per-client notes, retros, what actually happened
```

Required frontmatter:

```yaml
---
title: Engagement Kickoff Runbook
description: One sentence summarizing the page. Minimum 20 characters.
tags: [runbook, delivery]      # controlled vocabulary, see src/content.config.ts
status: draft                  # draft | published | archived
visibility: internal           # internal | shareable
owner: ah
updated: 2026-07-28
reviewCycleMonths: 3
order: 10
related: [engagement-model]
---
```

Full authoring guide: [Contributing to the Knowledge Base](content/onboarding/contributing.md).

## How this differs from a public docs site

Most of the conventions you would expect from a public documentation site are
deliberately absent, because they exist to serve external crawlers:

| Convention | Status | Why |
|---|---|---|
| `llms.txt`, sitemap, JSON-LD, OG tags | Removed | No crawlers to serve |
| `audience` build gate | Removed | Everything here is internal; nothing to gate |
| Drafts hidden from the build | Inverted | Drafts render with a banner — teams collaborate on WIP |
| Hand-written section overviews | Generated | The team knows what "Runbooks" means; generated listings can't drift |
| Staleness tracking | Added | Internal docs rot silently with no external pressure |
| Ownership enforcement | Added | Every page has an accountable maintainer, checked at build time |

`/index.json` survives and matters more here than it would publicly: it is the
ingestion surface for our own RAG and agent tooling, and it exposes `status` and
`isStale` so a pipeline can down-rank content we already know is unreliable.

Reasoning in full: [ADR 0001](content/decisions/0001-internal-only-knowledge-base.md).

## Build gates

`npm run build` fails on:

- Invalid frontmatter or a tag outside the controlled vocabulary
- A missing or unknown `owner`
- A broken internal link
- A redirect pointing at a page that does not exist
- An incomplete `/index.json`

Pages past their review cycle produce a **warning**, not a failure — staleness
should be visible without blocking unrelated work.

## Renaming a page

Add the old path to `redirects.json`. CI verifies every destination resolves, so
a rename without a redirect fails the build.

## Deployment

Publishing is manual by design. `.github/workflows/portal-deploy.yml` runs only
on `workflow_dispatch` so internal content is never published as a side effect of
a content commit.

> **Before publishing anywhere:** confirm the hosting target is access-controlled.
> This corpus contains rate cards and client specifics.
