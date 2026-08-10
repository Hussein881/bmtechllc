/**
 * Surfaces "this page has a change awaiting review" on the rendered site.
 *
 * The site is a static build of `main`, so it has no knowledge of open pull
 * requests. This fills that gap from the browser. The repo is public, so the
 * list endpoint works with no credential — a token is used only if one happens
 * to be cached, purely for the higher rate limit.
 *
 * Cost control matters here: unauthenticated GitHub API calls are limited to
 * 60/hour per IP. So this fetches the *whole* open-PR list once and caches it,
 * rather than querying per page — browsing the site costs one call per minute
 * at most, regardless of how many pages are visited.
 */

const OWNER = 'Hussein881';
const REPO = 'bmtechllc';
const CACHE_KEY = 'bmtech-open-prs';
const CACHE_MS = 60_000;

export type ChangeKind = 'delete' | 'edit' | 'add';

export interface PendingChange {
  kind: ChangeKind;
  number: number;
  url: string;
  /** Repo-relative path of the page the PR touches. */
  path: string;
}

interface PullSummary {
  number: number;
  html_url: string;
  body: string | null;
  head: { ref: string };
}

/**
 * Both facts come from the single list response, so no per-PR follow-up call
 * is needed: the branch name encodes the operation (see github-content-client)
 * and the PR body carries the exact path it touches.
 */
function classify(pull: PullSummary): PendingChange | null {
  const ref = pull.head?.ref ?? '';
  if (!ref.startsWith('pages/')) return null;

  const pathMatch = /- Path: `([^`]+)`/.exec(pull.body ?? '');
  if (!pathMatch) return null;

  const kind: ChangeKind = ref.startsWith('pages/delete-')
    ? 'delete'
    : ref.startsWith('pages/edit-')
      ? 'edit'
      : 'add';

  return { kind, number: pull.number, url: pull.html_url, path: pathMatch[1]! };
}

async function loadOpenChanges(): Promise<PendingChange[]> {
  const cached = sessionStorage.getItem(CACHE_KEY);
  if (cached) {
    try {
      const { at, changes } = JSON.parse(cached) as { at: number; changes: PendingChange[] };
      if (Date.now() - at < CACHE_MS) return changes;
    } catch {
      // Corrupt cache entry — fall through and refetch.
    }
  }

  const headers: Record<string, string> = { accept: 'application/vnd.github+json' };
  const token = sessionStorage.getItem('bmtech-portal-gh-token');
  if (token) headers.authorization = `Bearer ${token}`;

  const response = await fetch(
    `https://api.github.com/repos/${OWNER}/${REPO}/pulls?state=open&per_page=100`,
    { headers }
  );
  if (!response.ok) throw new Error(`GitHub returned ${response.status}`);

  const pulls = (await response.json()) as PullSummary[];
  const changes = pulls.map(classify).filter((c): c is PendingChange => c !== null);
  sessionStorage.setItem(CACHE_KEY, JSON.stringify({ at: Date.now(), changes }));
  return changes;
}

/**
 * Pending changes against one page, newest first. Resolves to an empty array
 * rather than rejecting: a rate-limited or offline lookup should leave the
 * page exactly as it would have been, never break it.
 */
export async function getPendingChanges(path: string): Promise<PendingChange[]> {
  try {
    const changes = await loadOpenChanges();
    return changes.filter((c) => c.path === path).sort((a, b) => b.number - a.number);
  } catch {
    return [];
  }
}

/** Drop the cache so a change just made by this user shows up immediately. */
export function invalidatePendingChanges(): void {
  sessionStorage.removeItem(CACHE_KEY);
}
