/// <reference path="../.astro/types.d.ts" />

interface ImportMetaEnv {
  /** Client ID of the GitHub App (Device Flow enabled) used for in-browser page authoring. */
  readonly PUBLIC_GITHUB_APP_CLIENT_ID?: string;
  /** Base URL of the device-flow-relay worker — see device-flow-relay/ and docs/github-app-setup.md. */
  readonly PUBLIC_GITHUB_DEVICE_FLOW_RELAY_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
