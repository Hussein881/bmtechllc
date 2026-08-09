# GitHub App setup for in-browser page authoring

The portal's `/new/`, `/edit/`, and per-page "Delete page" actions write directly
to this repo from the browser — no backend service is involved. That only
works once a GitHub App with **Device Flow** enabled exists and its Client ID
is set at build time. This is a one-time setup step; nothing needs to be
hosted or kept running afterward.

## 1. Create the App

GitHub → Settings → Developer settings → **GitHub Apps** → **New GitHub App**.

- **GitHub App name**: anything recognizable, e.g. `bmtechllc-portal-authoring`
- **Homepage URL**: the portal URL (e.g. `https://hussein881.github.io/bmtechllc/portal/`)
- **Callback URL**: not used by Device Flow — any placeholder is fine
- **Webhook**: uncheck "Active" — this App never receives events
- **Identifying and authorizing users** → check **"Request user authorization
  (OAuth) during installation"** off (not needed); instead scroll to
  **Device Flow** and check **"Enable Device Flow"**
- **Permissions** → Repository permissions:
  - **Contents**: Read and write
  - **Pull requests**: Read and write
  - **Metadata**: Read-only (auto-selected)
  - Leave every other permission as "No access"
- **Where can this GitHub App be installed?** → "Only on this account"

Click **Create GitHub App**.

## 2. Install it on this repo

On the App's settings page, click **Install App**, choose this account, and
select **Only select repositories** → `bmtechllc`.

## 3. Configure the portal build

Copy the **Client ID** shown on the App's settings page (starts with `Iv1.` or
similar — it is not a secret, it's safe to embed in a static build) and set it
as a build-time environment variable:

```bash
PUBLIC_GITHUB_APP_CLIENT_ID=<client id> npm run build
```

Or add it to whatever CI environment runs `deploy-pages.yml`. Without this
variable, `/new/` and `/edit/` render a "not configured" notice and Edit/Delete
buttons are hidden — the rest of the portal is unaffected.

## 4. Branch protection

Since anyone who authorizes through this flow can open a PR against `main`,
confirm branch protection on `main` requires review and passing
`portal-ci.yml` before merge — the same protection that already applies to
every other change to this repo.

## How it authenticates

Each authoring action (create, edit, delete) triggers GitHub's Device Flow: the
browser gets a short code, the user enters it at `github.com/login/device`,
and GitHub issues a token scoped to that person's own permissions on this
repo. The token lives only in `sessionStorage` for the current tab and is
never sent anywhere but `api.github.com`.
