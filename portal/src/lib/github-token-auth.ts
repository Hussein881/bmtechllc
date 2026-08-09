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

function renderDialog(): Promise<string> {
  return new Promise((resolve, reject) => {
    const dialog = document.createElement('dialog');
    dialog.className = 'gh-auth-dialog';
    dialog.innerHTML = `
      <p class="eyebrow">GitHub access needed</p>
      <p>
        Create a fine-grained token at
        <a href="${TOKEN_SETTINGS_URL}" target="_blank" rel="noreferrer">github.com/settings/personal-access-tokens/new</a>,
        scoped to the <strong>Hussein881/bmtechllc</strong> repository only, with
        <strong>Contents</strong> and <strong>Pull requests</strong> permissions set to
        Read and write. Then paste it below.
      </p>
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
      sessionStorage.setItem(STORAGE_KEY, token);
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
 * Resolves with a GitHub token, prompting the user to paste one if it isn't
 * already cached for this tab session.
 */
export async function getAccessToken(): Promise<string> {
  const cached = sessionStorage.getItem(STORAGE_KEY);
  if (cached) return cached;
  return renderDialog();
}

/** Forget the cached token, e.g. after a 401 from the GitHub API. */
export function clearCachedToken(): void {
  sessionStorage.removeItem(STORAGE_KEY);
}
