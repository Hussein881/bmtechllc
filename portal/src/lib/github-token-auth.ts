/**
 * The portal has no backend, so authoring writes go straight from the
 * browser to the GitHub REST API (which allows cross-origin calls) using a
 * token the user supplies themselves — a fine-grained Personal Access Token
 * scoped to just this repo. This avoids needing any separately hosted
 * service: GitHub's OAuth/device-flow *login* endpoints don't send CORS
 * headers (verified against the live endpoints), so a browser page can't
 * complete that flow directly, but a token pasted in by the person who owns
 * it sidesteps the login step entirely. Stored only in sessionStorage for
 * the current tab; never sent anywhere but api.github.com.
 */

const STORAGE_KEY = 'bmtech-portal-gh-token';
const TOKEN_SETTINGS_URL = 'https://github.com/settings/personal-access-tokens/new';
// Named here rather than imported from github-content-client to avoid a cycle:
// that module imports this one.
const REPO_SLUG = 'Hussein881/bmtechllc';

function renderDialog(): Promise<string> {
  return new Promise((resolve, reject) => {
    const dialog = document.createElement('dialog');
    dialog.className = 'gh-auth-dialog';
    dialog.innerHTML = `
      <p class="eyebrow">GitHub access needed</p>
      <p><a href="${TOKEN_SETTINGS_URL}" target="_blank" rel="noreferrer">Create a fine-grained token</a> with:</p>
      <ul class="gh-auth-perms">
        <li>Repository access — <strong>${REPO_SLUG}</strong> only</li>
        <li>Contents — <strong>Read and write</strong></li>
        <li>Pull requests — <strong>Read and write</strong></li>
      </ul>
      <p class="gh-auth-hint">Leave Account permissions untouched.</p>
      <input type="password" class="gh-token-input" placeholder="github_pat_…" autocomplete="off" spellcheck="false" />
      <p class="gh-auth-status"></p>
      <div class="gh-auth-actions">
        <button type="button" class="btn-secondary gh-auth-cancel">Cancel</button>
        <button type="button" class="btn-primary gh-auth-submit">Continue</button>
      </div>
    `;
    document.body.appendChild(dialog);
    dialog.showModal();

    const input = dialog.querySelector<HTMLInputElement>('.gh-token-input')!;
    const status = dialog.querySelector<HTMLElement>('.gh-auth-status')!;
    input.focus();

    const cleanup = () => { dialog.close(); dialog.remove(); };

    const cancel = () => {
      cleanup();
      reject(new Error('GitHub access was not provided.'));
    };
    dialog.querySelector('.gh-auth-cancel')?.addEventListener('click', cancel);
    dialog.addEventListener('cancel', cancel);

    const submit = () => {
      const token = input.value.trim();
      if (!token) {
        status.textContent = 'Paste a token first.';
        return;
      }
      // Deliberately not cached here — a token is only remembered once it has
      // actually completed a request (see rememberToken), so a token with the
      // wrong permissions re-prompts instead of silently failing all session.
      cleanup();
      resolve(token);
    };
    dialog.querySelector('.gh-auth-submit')?.addEventListener('click', submit);
    input.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') {
        event.preventDefault();
        submit();
      }
    });
  });
}

/**
 * Resolves with a GitHub token, prompting the user to paste one if a working
 * one isn't already cached for this tab session.
 */
export async function getAccessToken(): Promise<string> {
  const cached = sessionStorage.getItem(STORAGE_KEY);
  if (cached) return cached;
  return renderDialog();
}

/** Cache a token that has now proven it works, so the tab stops asking. */
export function rememberToken(token: string): void {
  sessionStorage.setItem(STORAGE_KEY, token);
}

/** Whether this tab is currently holding a token. */
export function hasCachedToken(): boolean {
  return sessionStorage.getItem(STORAGE_KEY) !== null;
}

/** Forget the cached token, e.g. after GitHub rejects it. */
export function clearCachedToken(): void {
  sessionStorage.removeItem(STORAGE_KEY);
}
