---
title: Adding a Page From the Portal
description: Step-by-step instructions for creating, editing, or deleting a knowledge-base page directly in the browser, including how to generate the GitHub token it asks for.
tags: [runbook, tooling, onboarding, process]
status: published
visibility: internal
owner: team
updated: 2026-08-09
reviewCycleMonths: 6
order: 15
related: [portal-authoring-architecture]
---

You can add, edit, and delete pages without cloning the repo or touching a
terminal. Everything happens in the browser, and nothing you do publishes
immediately — every change opens a pull request that a person reviews first.

If you would rather work from a local checkout, add a Markdown file under
`portal/content/<section>/` and open a pull request the usual way.

## One-time setup: generate a GitHub token

The portal asks for a token the first time you submit something in a browser
session. Generate one before you start so you are not interrupted mid-draft.

1. Go to
   [github.com/settings/personal-access-tokens/new](https://github.com/settings/personal-access-tokens/new).
2. **Token name** — anything you will recognize later, e.g. `portal authoring`.
3. **Expiration** — pick what you are comfortable with. GitHub caps
   fine-grained tokens at one year.
4. **Repository access** — choose **Only select repositories**, then select
   **`Hussein881/bmtechllc`**.
5. **Repository permissions** — set exactly these two:

   | Permission | Access |
   |---|---|
   | Contents | Read and write |
   | Pull requests | Read and write |

   `Metadata: Read-only` is added automatically and cannot be removed. That is
   expected. Leave every other permission at **No access**.

6. Leave the **Account permissions** section completely alone.
7. Click **Generate token**, then copy it. GitHub shows it only once.

> [!IMPORTANT]
> Treat the token like a password. Do not paste it into a document, a chat
> message, or a page in this knowledge base.

### If your token is rejected

The most common cause is **Contents** being left at Read-only, which blocks the
step that creates a branch. Edit the token, correct the permission, and try
again — editing an existing token keeps the same token string and takes effect
immediately.

## Creating a page

1. Open the section the page belongs in, e.g.
   [Runbooks](/bmtechllc/portal/runbooks/). Each section page states what
   belongs in it if you are unsure.
2. Click **Add a page**.
3. Fill in the form:

   | Field | Notes |
   |---|---|
   | Section | Pre-filled from where you clicked; change it if needed |
   | Title | Becomes the page's permanent URL, so choose deliberately |
   | Description | At least 20 characters. This is what search and retrieval tools show |
   | Owner | Your initials — must be a known owner, or the build will fail |
   | Markdown | The page body |

4. Watch the **Safe preview** panel as you type. It shows the exact file path
   your title will produce and a rough render of your Markdown.
5. Click **Create review pull request**.
6. Paste your token if prompted.
7. On success, the message area shows a link to your new pull request.

New pages are created as `status: draft`, internal, untagged. Add tags,
change status, or set related pages later using **Edit page**.

> [!NOTE]
> Raw HTML is rejected. Angle brackets inside code blocks or backticks are
> fine — `<placeholder>` in a code sample will not trip it.

## Editing a page

1. Open the page.
2. Click **Edit page** at the bottom.
3. The form opens pre-filled with the current content. Unlike creating, this
   form exposes every field: status, visibility, tags, review cycle, order,
   and related pages.
4. Click **Update via pull request**.

## Deleting a page

1. Open the page and click **Delete page**.
2. Read the confirmation carefully. If other pages link to this one, the
   warning lists them by name.
3. Confirm.

> [!WARNING]
> If the confirmation warns that other pages link to this one, the pull
> request **will fail its build check** until those links are removed too.
> Either edit those pages first, or expect to fix them on the branch
> afterwards. Broken internal links block the merge.

## After you submit

Your change is on a branch, in a pull request — it is not live yet.

1. **Automated checks run.** These validate frontmatter, tag vocabulary, the
   owner name, and every internal link. A red check means something needs
   fixing before the page can merge.
2. **A person reviews it.** Required — nobody merges their own work
   unreviewed.
3. **On merge, the site rebuilds** and your page appears.

While a change is waiting, anyone visiting that page sees a banner saying an
edit or deletion is pending, linking to the pull request.

## Common problems

| What you see | What it means |
|---|---|
| Clicking submit seems to do nothing | Scroll up — a validation message is waiting at the top of the form. Most often the description is under 20 characters |
| "Raw HTML is not allowed" | You have an HTML tag in the body outside a code block |
| "That token was rejected by GitHub" | Token permissions are wrong — see the setup section above |
| "A page with this title already exists" | Pick a different title, or edit the existing page instead |
| Wrong token cached | Click **Use a different GitHub token** next to the submit button |

## How this works underneath

See
[Portal Authoring Architecture](/bmtechllc/portal/guide/portal-authoring-architecture/).
