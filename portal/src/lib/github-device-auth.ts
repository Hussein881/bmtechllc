/**
 * Browser-only GitHub App device flow. No client secret is involved — this is
 * the same mechanism the `gh` CLI uses. The resulting token is scoped to the
 * signed-in user's own permissions on the repo; the portal never holds or
 * requests an elevated credential.
 *
 * GitHub's login/device/code and login/oauth/access_token do not send
 * Access-Control-Allow-Origin, so a browser page can't call them directly —
 * verified against the live endpoints. device-flow-relay/ forwards the two
 * requests and adds that header; it holds no secret and makes no auth
 * decision of its own. See docs/github-app-setup.md.
 */
const RELAY_BASE = (import.meta.env.PUBLIC_GITHUB_DEVICE_FLOW_RELAY_URL ?? '').replace(/\/$/, '');
const DEVICE_CODE_URL = `${RELAY_BASE}/device/code`;
const TOKEN_URL = `${RELAY_BASE}/oauth/token`;
const STORAGE_KEY = 'bmtech-portal-gh-token';

interface DeviceCodeResponse {
  device_code: string;
  user_code: string;
  verification_uri: string;
  expires_in: number;
  interval: number;
}

interface TokenResponse {
  access_token?: string;
  error?: string;
  error_description?: string;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function renderDialog(info: DeviceCodeResponse): { dialog: HTMLDialogElement; setStatus: (text: string) => void } {
  const dialog = document.createElement('dialog');
  dialog.className = 'gh-auth-dialog';
  dialog.innerHTML = `
    <p class="eyebrow">Sign in with GitHub</p>
    <p>Open <a href="${info.verification_uri}" target="_blank" rel="noreferrer">${info.verification_uri}</a> and enter this code:</p>
    <p class="gh-auth-code">${info.user_code}</p>
    <p class="gh-auth-status">Waiting for authorization&hellip;</p>
    <button type="button" class="btn-secondary gh-auth-cancel">Cancel</button>
  `;
  document.body.appendChild(dialog);
  dialog.showModal();
  const status = dialog.querySelector('.gh-auth-status') as HTMLElement;
  return { dialog, setStatus: (text) => { status.textContent = text; } };
}

/**
 * Resolves with a GitHub user access token, prompting the user to authorize
 * via GitHub's device flow if one isn't already cached for this tab session.
 */
export async function getAccessToken(clientId: string): Promise<string> {
  if (!RELAY_BASE) throw new Error('GitHub sign-in is not configured (PUBLIC_GITHUB_DEVICE_FLOW_RELAY_URL is unset).');

  const cached = sessionStorage.getItem(STORAGE_KEY);
  if (cached) return cached;

  // GitHub Apps don't take an OAuth `scope` here — permissions come from
  // what the App itself was granted (Contents + Pull requests) when installed.
  const codeResponse = await fetch(DEVICE_CODE_URL, {
    method: 'POST',
    headers: { accept: 'application/json', 'content-type': 'application/json' },
    body: JSON.stringify({ client_id: clientId }),
  });
  if (!codeResponse.ok) throw new Error('Could not start GitHub sign-in.');
  const codeData = (await codeResponse.json()) as DeviceCodeResponse;

  const { dialog, setStatus } = renderDialog(codeData);
  let cancelled = false;
  const onCancel = () => { cancelled = true; dialog.close(); };
  dialog.querySelector('.gh-auth-cancel')?.addEventListener('click', onCancel);
  dialog.addEventListener('cancel', onCancel);

  try {
    const intervalMs = Math.max(codeData.interval, 5) * 1000;
    const deadline = Date.now() + codeData.expires_in * 1000;

    while (Date.now() < deadline) {
      await sleep(intervalMs);
      if (cancelled) throw new Error('GitHub sign-in was cancelled.');

      const tokenResponse = await fetch(TOKEN_URL, {
        method: 'POST',
        headers: { accept: 'application/json', 'content-type': 'application/json' },
        body: JSON.stringify({
          client_id: clientId,
          device_code: codeData.device_code,
          grant_type: 'urn:ietf:params:oauth:grant-type:device_code',
        }),
      });
      const tokenData = (await tokenResponse.json()) as TokenResponse;

      if (tokenData.access_token) {
        sessionStorage.setItem(STORAGE_KEY, tokenData.access_token);
        setStatus('Signed in.');
        return tokenData.access_token;
      }
      if (tokenData.error === 'authorization_pending') continue;
      if (tokenData.error === 'slow_down') { await sleep(intervalMs); continue; }
      throw new Error(tokenData.error_description || 'GitHub sign-in failed.');
    }
    throw new Error('GitHub sign-in timed out.');
  } finally {
    dialog.close();
    dialog.remove();
  }
}

/** Forget the cached token, e.g. after a 401 from the GitHub API. */
export function clearCachedToken(): void {
  sessionStorage.removeItem(STORAGE_KEY);
}
