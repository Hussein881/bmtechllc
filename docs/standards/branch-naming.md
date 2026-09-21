# Branch naming standard

Use this convention for all new manually created work branches in this repository, across projects and documentation. Consistent names make the purpose and related ticket visible during review.

## Format

```text
<type>/<ticket-id>-<short-description>
<type>/<short-description>                  # when no ticket exists
```

- Use exactly one `/` to separate the type from the rest of the name.
- Use lowercase ASCII letters, digits, and single hyphens for the description. Use hyphens between words; no spaces, underscores, dots, additional slashes, or repeated/trailing hyphens.
- Keep the description short and specific, such as `portal-login-error`. Include the project or component when useful in this multi-project repository.
- Use lowercase for the type and description. Preserve the canonical casing of an external ticket key (for example, `BM-123`) so integrations can recognize it.
- Include a ticket identifier when one exists. For a GitHub issue, use its number without `#`; for an external tracker, use the full key. Never invent a ticket number or use placeholder IDs in a real branch.
- Do not include personal names, credentials, private client details, or other sensitive information in branch names.

## Standard prefixes

Choose the prefix that best describes the main purpose of the change. Supporting tests or documentation stay on the same branch as the change they support.

| Prefix | Purpose | Example |
| --- | --- | --- |
| `feature/` | Add or extend functionality | `feature/123-portal-search` |
| `fix/` | Correct a bug | `fix/124-portal-login-error` |
| `chore/` | Maintenance, dependencies, build, or CI configuration | `chore/update-portal-dependencies` |
| `docs/` | Documentation-only changes | `docs/branch-naming-convention` |
| `refactor/` | Restructure code without changing behavior | `refactor/125-extract-content-client` |
| `test/` | Add or improve tests without a feature or bug fix | `test/126-cover-page-deletion` |

Ticket numbers and keys in these examples are illustrative. Do not use a person's name, project name, or tool name as a prefix; put useful project context in the description instead.

## Project tracking

- GitHub issue example: `fix/124-portal-login-error`. Link the actual issue in the pull request description. Use `Closes #124` only when the PR fully resolves that issue; use `Refs #124` for related or partial work.
- External tracker example: `feature/BM-123-portal-search`. Repeat the exact ticket key and link in the PR description. A branch name alone does not configure an integration or guarantee a ticket status change.
- For issues in another repository, include the full issue URL in the PR description to avoid ambiguity.
- If a change covers several tickets, use the primary ticket in the branch name and link all relevant tickets in the PR description.
- If no ticket exists, omit the identifier: `docs/branch-naming-convention`.

## Examples to avoid

| Avoid | Use instead | Reason |
| --- | --- | --- |
| `Feature/123-Add_Search` | `feature/123-add-search` | Lowercase type and description; hyphens between words |
| `fix/#124-login` | `fix/124-login` | Omit the GitHub `#` marker |
| `portal/search` | `feature/portal-search` | Use a standard purpose prefix |
| `feature/123/portal-search` | `feature/123-portal-search` | Only one slash |
| `docs/update` | `docs/branch-naming-convention` | Describe the specific change |

## Workflow and adoption

1. Start from an up-to-date `main` unless the work explicitly depends on another branch.
2. Select the prefix, add the real ticket ID if available, and write a short description.
3. Create the branch, for example: `git switch -c docs/branch-naming-convention`.
4. Open a pull request targeting `main` (or the agreed dependency branch), include ticket links, and check the name during review.

This is a documented review convention; this change does not introduce an automated naming check. Apply it to new branches. Existing branches may finish under their current names to avoid disrupting open PRs and collaborators. The long-lived `main` branch is exempt.

### Portal-generated branches

The portal reserves `pages/` for automatically generated authoring branches:

```text
pages/<section>-<slug>-<timestamp>
pages/edit-<slug>-<timestamp>
pages/delete-<slug>-<timestamp>
```

These are an explicit tooling exception: the [content client](../../portal/src/lib/github-content-client.ts) generates the names, and [pending-change detection](../../portal/src/lib/pending-changes.ts) reads the prefix to classify operations. Leave generated names intact and do not use `pages/` for manual work. Any future change to this scheme must update both components together.
