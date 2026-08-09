---
title: Portal Authoring Architecture
description: How the portal's in-browser create, edit, and delete features actually work — what runs where, why a token is required, and what happens between clicking submit and a page going live.
tags: [reference, tooling, infrastructure, security]
status: published
visibility: internal
owner: team
updated: 2026-08-09
reviewCycleMonths: 12
order: 40
related: [adding-a-page-from-the-portal, adding-a-page]
---

This explains what happens when you use **Add a page**, **Edit page**, or
**Delete page**. For the steps themselves, see
[Adding a Page From the Portal](/bmtechllc/portal/runbooks/adding-a-page-from-the-portal/).

## The constraint everything follows from

This portal is a **static site**. The build turns Markdown files into plain
HTML, and GitHub Pages serves those files. There is no application server
behind it, no database, and nothing running that could receive a form
submission.

That single fact explains every design decision below. A normal web app would
POST your form to a server that writes to a database. Here there is no server
to POST to — so the browser talks to GitHub's API directly, and **GitHub is
the database**.

## What happens when you click submit

Your browser performs four API calls in sequence, using your token:

1. **Check for a conflict** — does a file already exist at that path?
2. **Create a branch** off `main`, named for the operation, e.g.
   `pages/runbooks-my-new-page-20260809231400`.
3. **Commit the file** to that branch. Your form fields become YAML
   frontmatter; the Markdown box becomes the body.
4. **Open a pull request** from that branch back to `main`.

Editing and deleting follow the same shape — the middle step becomes an update
or a delete. Every path ends at a pull request. **Nothing ever writes to
`main` directly.**

## Why it asks for a token

GitHub needs to know who you are before letting you write to the repository.
The usual approach is a "Sign in with GitHub" button, but that flow requires a
server-side component to complete the handshake, and a static site has none.

Two consequences:

- You supply a **fine-grained personal access token** yourself. It carries
  your own permissions — the portal cannot grant you access you do not
  already have.
- The token is scoped to this one repository, with only Contents and Pull
  requests write access. It cannot touch your other repositories or your
  account settings.

### Where the token lives

In `sessionStorage`, which is per-tab and cleared when you close the tab. It
is sent only to `api.github.com`, never to any other server — there is no
other server.

Two behaviors worth knowing:

- A token is **only remembered after it successfully completes a request**. A
  token with wrong permissions is discarded rather than cached, so you are
  re-prompted instead of hitting the same failure repeatedly.
- If GitHub later rejects a cached token (expired, revoked, permissions
  changed), it is dropped automatically and you are asked for a new one.

## Why nothing publishes immediately

The pull request is the review boundary, and two gates sit on it:

**Automated checks** run the full build. They fail on invalid frontmatter, a
tag outside the controlled vocabulary, an unknown owner, a broken internal
link, or an incomplete `index.json`.

**Human review** is required by branch protection on `main`. Approval plus
passing checks are both required before merge.

This is why deleting a page that others link to fails: removing the file
leaves dangling links, and the link check refuses to let that merge. The
delete confirmation warns about this before creating the PR, but the gate is
what actually enforces it.

## Pending-change banners

Because the site is a static build of `main`, it has no inherent knowledge of
open pull requests. So each page, once loaded, asks GitHub for the list of
open PRs and shows a banner if one touches that page.

Two details make this cheap:

- **One request covers the whole site.** The full list of open PRs is fetched
  once and cached briefly, rather than querying per page. Browsing many pages
  costs roughly one request per minute.
- **It reads without credentials.** The repository is public, so this works
  with no token. If the lookup fails — rate limit, offline — the banner
  silently does not render rather than breaking the page.

The operation and target path come from the branch name and PR body, both
present in that single list response, so no follow-up call per PR is needed.

## What is deliberately not here

| Not built | Why |
|---|---|
| A backend service | Nothing to deploy, monitor, or pay for; GitHub already does this work |
| "Sign in with GitHub" | Requires a server-side component the static site cannot host |
| Direct publishing | Review is the point; a bypass would defeat it |
| WYSIWYG editing | Markdown files are the source of truth and stay diffable in Git |

## Where the code lives

| File | Responsibility |
|---|---|
| `src/pages/new.astro` | Create form and preview |
| `src/pages/edit.astro` | Edit form, pre-filled from the page you came from |
| `src/layouts/DocsLayout.astro` | Edit/Delete buttons and pending banners |
| `src/lib/github-content-client.ts` | The GitHub API calls and token lifecycle |
| `src/lib/github-token-auth.ts` | Token prompt and per-tab storage |
| `src/lib/pending-changes.ts` | Open-PR lookup and caching |
