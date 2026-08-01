# Page authoring service

This is the authenticated write boundary for the static portal. It is a Fetch handler suitable for a Cloudflare Worker or Vercel Edge Function; deploy it separately from GitHub Pages. The browser never receives a GitHub credential.

## Required configuration

Copy `.env.example` into the deployment provider's secret/environment store. Set `PUBLIC_PAGE_AUTHORING_API_URL` in the portal build to this service URL and `PUBLIC_PAGE_AUTHORING_LOGIN_URL` to the identity provider's login entrypoint.

The service accepts only a Bearer OIDC access token whose issuer, audience, and signature match `OIDC_*`. It then requires the token's stable `sub` claim to be in the explicit comma-separated `OIDC_ALLOWED_SUBJECTS` allowlist; wildcards and an empty list are rejected at startup. The static page calls an optional `window.BMTECH_PORTAL_AUTH.getAccessToken()` integration to obtain that short-lived token (or can use a same-origin session gateway); it intentionally does not hold an OAuth client secret. Configure CORS `ALLOWED_ORIGIN` to the exact portal origin.

Create and install a GitHub App on this repository with **Contents: Read & Write** and **Pull requests: Read & Write** only. Its installation token is short-lived. Branch protection must require review and Portal CI before merge.

## Local verification

```bash
npm install
npm run validate
```

Tests use an in-memory GitHub writer; no GitHub App credential or network write is required. Production audit events deliberately include identity, section, slug, and PR number—not Markdown content.
