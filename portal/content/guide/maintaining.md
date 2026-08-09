---
title: Maintaining the Knowledge Base
description: How to keep the knowledge base trustworthy over time — handling stale pages, renaming safely, archiving, and the build gates that enforce it.
tags: [process, tooling, reference]
status: published
visibility: internal
owner: ah
updated: 2026-07-28
reviewCycleMonths: 12
order: 40
related: [frontmatter-reference]
---

# Maintaining the Knowledge Base

A knowledge base fails slowly. Nobody deletes it; it just accumulates pages that
used to be true until people stop trusting any of it. Everything below exists to
delay that.

## The staleness loop

Every page declares how fast it decays via `reviewCycleMonths`. Once `updated`
is older than that window, three things happen automatically:

1. The page renders a **Review overdue** banner
2. It appears in **Needs review** on the home page
3. `npm run build` prints it as a warning
4. `/index.json` marks it `isStale: true`, so internal tooling can down-rank it

This is a warning, never a build failure. Blocking someone's unrelated work
because a different page went stale trains people to ignore the signal.

### Reviewing a page

Read it and pick one:

| Situation | Action |
|---|---|
| Still accurate | Bump `updated`. That is the whole review |
| Mostly accurate | Fix the drift, bump `updated` |
| No longer how we work | Set `status: archived` and write why at the top |
| Was never used | Delete it, add a redirect if anything linked to it |

Bumping `updated` on a page you have actually reread is not gaming the metric —
it is the metric working. Bumping it without reading is how the signal dies.

## Renaming and moving

URLs are addresses teammates bookmark and tooling stores. Renaming without a
redirect breaks them silently.

Add the old path to `redirects.json`:

```json
{
  "redirects": {
    "/services/ai-readiness-assessment": "/playbooks/scoping-readiness-assessment/"
  }
}
```

CI verifies every destination resolves to a real page, so a redirect pointing at
a deleted page fails the build.

> [!WARNING]
> Redirects are permanent. Once one exists, leave it — the cost of keeping it is
> two lines of JSON, and the cost of removing it is a broken link you will never
> hear about.

## Archiving vs. deleting

**Archive** when the page describes something we genuinely used to do. Old
decisions are frequently the missing context for a current one, and an archived
page with a banner is more useful than a dead link.

**Delete** when the page was never real — an abandoned draft, a duplicate, notes
that went nowhere. Add a redirect if anything linked to it.

## What the build enforces

`npm run build` fails on:

| Check | Why it exists |
|---|---|
| Frontmatter schema | A page missing `description` is unsummarizable and unsearchable |
| Controlled tag vocabulary | Free-form tags fragment into near-duplicates |
| Known owner | Typos silently orphan pages |
| Internal links resolve | Broken links are invisible until someone clicks |
| Redirect destinations resolve | A redirect to a deleted page is worse than no redirect |
| `/index.json` completeness | Internal tooling depends on it being well-formed |

And warns on:

| Check | Why it is a warning |
|---|---|
| Pages past their review cycle | Visibility without blocking unrelated work |

## Adding to the tag vocabulary

Edit the `TAGS` array in `src/content.config.ts`:

```typescript
export const TAGS = [
  'ai-strategy',
  'rag',
  // ...
  'your-new-tag',
] as const;
```

Before adding one, check whether an existing tag covers it. The vocabulary is
closed so that filtering stays meaningful — a tag used on one page is noise.

## Adding an owner

Edit `KNOWN_OWNERS` in `scripts/check-build.mjs`. Use initials, matching the
convention already in use.
