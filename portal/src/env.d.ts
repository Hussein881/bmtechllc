/// <reference path="../.astro/types.d.ts" />

interface Window {
  /** Injected by the organization's OIDC/SSO integration; never contains a GitHub credential. */
  BMTECH_PORTAL_AUTH?: { getAccessToken?: () => Promise<string | undefined> };
}
