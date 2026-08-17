# Getting access to create, edit, or delete pages

The portal's `/new/`, `/edit/`, and per-page "Delete page" actions write
directly to this repo from the browser — no backend service, no hosted relay,
nothing beyond GitHub itself. That works by asking you for a **fine-grained
Personal Access Token** the first time you submit something, instead of a
"Sign in with GitHub" popup. This is a one-time step per browser session.

## Why a token instead of a sign-in button

GitHub's own sign-in pages (the ones behind a polished "Sign in with GitHub"
flow) don't allow a browser page to call them directly — that's a GitHub
platform limitation, not something this portal can configure around, and
fixing it would mean standing up a separately hosted relay service. GitHub's
actual write API (the part that creates branches, commits, and pull requests)
*does* allow direct browser calls, so a token you generate yourself sidesteps
the problem entirely: no relay, nothing to host, nothing to keep running.

## Create your token

1. Go to
   [github.com/settings/personal-access-tokens/new](https://github.com/settings/personal-access-tokens/new).
2. **Repository access** → **Only select repositories** → choose `bmtechllc`.
3. **Permissions** → **Repository permissions**:
   - **Contents**: Read and write
   - **Pull requests**: Read and write
   - Leave everything else as "No access".
4. Set an expiration you're comfortable with (GitHub caps fine-grained tokens
   at 1 year).
5. Generate the token and copy it — GitHub only shows it once.

## Using it

The first time you click "Create review pull request," "Update via pull
request," or "Delete page," the portal shows a small dialog asking for this
token. Paste it in. It's stored only in `sessionStorage` for that browser tab
— never sent anywhere except `api.github.com`, and gone as soon as the tab is
closed.

If a token expires or is revoked, the next write attempt will fail with a
401; the portal drops the cached token automatically and re-prompts.

## Branch protection

Anyone who authorizes with their own token can open a PR against `main`, but
can only do what their own GitHub permissions on the repo already allow —
this is standard GitHub token scoping, not something the portal enforces
itself. Branch protection on `main` (required review + passing
`portal-ci.yml`) is what actually gates whether that PR can be merged.
