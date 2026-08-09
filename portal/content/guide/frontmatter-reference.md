---
title: Frontmatter Reference
description: Every frontmatter field available on a knowledge base page, what it controls, whether it is required, and how to choose a sensible value.
tags: [reference, tooling, process]
status: published
visibility: internal
owner: ah
updated: 2026-07-28
reviewCycleMonths: 12
order: 20
related: [adding-a-page]
---

Frontmatter is validated against a schema at build time. A page that violates
the contract fails the build rather than rendering something subtly wrong.

The schema lives in `src/content.config.ts`.

## Required fields

### `title`

The page heading and its label everywhere it appears — sidebar, search results,
related links.

```yaml
title: Stakeholder Interview Playbook
```

Write it as a noun phrase describing the artifact, not a sentence.

### `description`

One sentence summarizing the page. Minimum 20 characters, enforced.

```yaml
description: A step-by-step guide for conducting stakeholder interviews during discovery, including question frameworks and synthesis methods.
```

This field does more work than it appears to. It is the search-result summary,
the section-listing blurb, and the retrieval abstract in `/index.json` that our
own agent tooling reads. Forcing every page to have one forces every page to be
summarizable — which is a quality gate in itself. If you cannot write this
sentence, the page is probably covering two topics.

### `owner`

Who is accountable for keeping this page true.

```yaml
owner: ah
```

Must match an entry in `KNOWN_OWNERS` in `scripts/check-build.mjs`. The build
fails on an unknown value, which catches typos that would otherwise silently
orphan a page.

### `updated`

The date of the last substantive change. Drives the staleness calculation.

```yaml
updated: 2026-07-28
```

Update it when the meaning changes, not for typo fixes.

## Optional fields

### `status`

Defaults to `draft`.

| Value | Renders | Meaning |
|---|---|---|
| `draft` | With a Draft banner | Work in progress, unverified |
| `published` | Normally | Reviewed and trusted |
| `archived` | With an Archived banner | Historical; do not follow it |

Unlike a public site, nothing is hidden from the build. Archived pages stay
reachable because old decisions are often exactly what you need to understand a
current one.

### `visibility`

Defaults to `internal`.

```yaml
visibility: shareable
```

`shareable` renders a badge marking the page as reviewed and safe to share
outside the firm. It is display-only — it does not publish anything. Publishing
means deliberately copying content into `website/`.

### `reviewCycleMonths`

Defaults to `6`. How long before the page is flagged as overdue for review.

```yaml
reviewCycleMonths: 3
```

Match it to how fast the content actually decays:

| Content | Suggested | Why |
|---|---|---|
| Runbooks, pricing | 3 | Tied to current tooling and rates |
| Playbooks, onboarding | 6 | Change as practice evolves |
| Methodology, reference | 12 | Deliberately stable |

Overdue pages produce a build **warning**, not a failure, and surface in the
"Needs review" list on the home page.

### `tags`

From the controlled vocabulary in `src/content.config.ts`. An unknown tag fails
the build.

```yaml
tags: [discovery, playbook, client-comms]
```

The vocabulary is closed on purpose. Free-form tags rot into near-duplicates —
`rag`, `RAG`, `retrieval` — that fragment search and filtering. Adding a tag is
a one-line change: cheap, but deliberate.

### `order`

Defaults to `50`. Controls position in the sidebar and section listings; lower
sorts first.

```yaml
order: 10
```

Leave gaps of 10 so you can insert pages later without renumbering. Ties break
alphabetically.

Ordering lives here rather than in filename prefixes (`01-intro.md`) because
prefixes leak into URLs and every reorder breaks links.

### `related`

Bare filenames of pages a reader would want next.

```yaml
related: [engagement-model, stakeholder-interviews]
```

These render as a **Related** block, and the target page automatically gains a
**Referenced by** entry pointing back — so a single edge makes the graph
navigable in both directions.

## Full example

```yaml
---
title: Engagement Kickoff Runbook
description: The sequence to run in the first week of a new engagement, from contract countersign through the first working session.
tags: [runbook, delivery, scoping]
status: draft
visibility: internal
owner: ah
updated: 2026-07-28
reviewCycleMonths: 3
order: 10
related: [engagement-model, readiness-checklist]
---
```
