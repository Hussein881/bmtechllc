import { Octokit } from '@octokit/rest';
import yaml from 'js-yaml';
import { getAccessToken, rememberToken, clearCachedToken } from './github-token-auth';

export const OWNER = 'Hussein881';
export const REPO = 'bmtechllc';
export const BASE_BRANCH = 'main';

export interface PageFrontmatter {
  title: string;
  description: string;
  tags: string[];
  status: string;
  visibility: string;
  owner: string;
  updated: string;
  reviewCycleMonths: number;
  order: number;
  related: string[];
}

export interface PullRequestResult {
  url: string;
  number: number;
}

const MAX_MARKDOWN_BYTES = 100_000;

export function slugify(title: string): string {
  return title
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '')
    .slice(0, 80);
}

/** Repo-relative path for a page — matches the glob loader base in content.config.ts. */
export function contentPath(section: string, slugOrId: string): string {
  return `portal/content/${section}/${slugOrId}.md`;
}

// Text inside fenced code blocks or inline code spans is never interpreted as
// HTML by the Markdown pipeline — it renders as literal text — so angle
// brackets there (e.g. a `<name>` placeholder in a path) are safe and common
// in technical writing. Only check what's left after stripping those out.
function stripCode(markdown: string): string {
  return markdown.replace(/```[\s\S]*?```/g, '').replace(/`[^`\n]*`/g, '');
}

function assertSafeMarkdown(body: string): void {
  if (/<\/?[a-z][^>]*>/i.test(stripCode(body))) throw new Error('Raw HTML is not allowed in Markdown. Use Markdown syntax instead.');
  if (new TextEncoder().encode(body).byteLength > MAX_MARKDOWN_BYTES) throw new Error('Markdown is too large.');
}

function renderMarkdown(frontmatter: PageFrontmatter, body: string): string {
  const yamlBlock = yaml.dump(frontmatter, { lineWidth: -1 }).trimEnd();
  return `---\n${yamlBlock}\n---\n\n${body.trim()}\n`;
}

function parseMarkdown(raw: string): { frontmatter: PageFrontmatter; body: string } {
  const match = /^---\n([\s\S]*?)\n---\n?([\s\S]*)$/.exec(raw);
  if (!match) throw new Error('That file does not have the expected frontmatter block.');
  const frontmatter = yaml.load(match[1]) as PageFrontmatter;
  return { frontmatter, body: match[2].trim() };
}

// atob/btoa operate on Latin1 strings; go through raw bytes to keep UTF-8 intact.
function toBase64(value: string): string {
  const bytes = new TextEncoder().encode(value);
  let binary = '';
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary);
}
function fromBase64(value: string): string {
  const binary = atob(value.replace(/\n/g, ''));
  const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
  return new TextDecoder().decode(bytes);
}

function timestampSuffix(): string {
  return new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 14);
}

/**
 * Runs a GitHub operation, and owns the token lifecycle around it: a token is
 * cached only once it has completed a real request, and is dropped the moment
 * GitHub rejects it. Without this, a token with the wrong permissions would be
 * remembered on sight and fail every subsequent attempt for the whole session.
 */
async function withGitHub<T>(operation: (octokit: Octokit) => Promise<T>): Promise<T> {
  const token = await getAccessToken();
  const octokit = new Octokit({ auth: token });
  try {
    const result = await operation(octokit);
    rememberToken(token);
    return result;
  } catch (error) {
    const status = (error as { status?: number }).status;
    // 401 = bad/expired credential, 403 = valid token without the required
    // permission. Both mean "this token won't do", so re-prompt next time.
    if (status === 401 || status === 403) {
      clearCachedToken();
      throw new Error(
        'That token was rejected by GitHub. It needs Contents and Pull requests set to "Read and write", ' +
          'and this repository selected under Repository access. You will be asked for a token again.'
      );
    }
    throw error;
  }
}

async function branchFromDefault(octokit: Octokit, branch: string): Promise<void> {
  const { data: ref } = await octokit.rest.git.getRef({ owner: OWNER, repo: REPO, ref: `heads/${BASE_BRANCH}` });
  await octokit.rest.git.createRef({ owner: OWNER, repo: REPO, ref: `refs/heads/${branch}`, sha: ref.object.sha });
}

async function pathExists(octokit: Octokit, path: string): Promise<boolean> {
  try {
    await octokit.rest.repos.getContent({ owner: OWNER, repo: REPO, path });
    return true;
  } catch (error) {
    if ((error as { status?: number }).status === 404) return false;
    throw error;
  }
}

export async function createPage(
  input: { section: string; frontmatter: PageFrontmatter; body: string }
): Promise<PullRequestResult> {
  assertSafeMarkdown(input.body);
  const slug = slugify(input.frontmatter.title);
  if (!slug) throw new Error('Title must contain at least one letter or number.');
  const path = contentPath(input.section, slug);

  return withGitHub(async (octokit) => {
    if (await pathExists(octokit, path)) {
      throw new Error('A page with this title already exists in that section.');
    }

    const branch = `pages/${input.section}-${slug}-${timestampSuffix()}`;
    await branchFromDefault(octokit, branch);
    await octokit.rest.repos.createOrUpdateFileContents({
      owner: OWNER,
      repo: REPO,
      path,
      branch,
      message: `docs(portal): add ${input.frontmatter.title}`,
      content: toBase64(renderMarkdown(input.frontmatter, input.body)),
    });
    const { data: pr } = await octokit.rest.pulls.create({
      owner: OWNER,
      repo: REPO,
      base: BASE_BRANCH,
      head: branch,
      title: `docs(portal): add ${input.frontmatter.title}`,
      body: `Proposed via the portal authoring UI.\n\n- Section: \`${input.section}\`\n- Path: \`${path}\``,
    });
    return { url: pr.html_url, number: pr.number };
  });
}

export async function fetchPage(
  path: string
): Promise<{ sha: string; frontmatter: PageFrontmatter; body: string }> {
  return withGitHub(async (octokit) => {
    const { data } = await octokit.rest.repos.getContent({ owner: OWNER, repo: REPO, path });
    if (Array.isArray(data) || data.type !== 'file' || !data.content) {
      throw new Error('Could not read that page from GitHub.');
    }
    const { frontmatter, body } = parseMarkdown(fromBase64(data.content));
    return { sha: data.sha, frontmatter, body };
  });
}

export async function updatePage(
  input: { path: string; sha: string; frontmatter: PageFrontmatter; body: string }
): Promise<PullRequestResult> {
  assertSafeMarkdown(input.body);
  const slug = input.path.split('/').pop()!.replace(/\.md$/, '');
  return withGitHub(async (octokit) => {
    const branch = `pages/edit-${slug}-${timestampSuffix()}`;
    await branchFromDefault(octokit, branch);
    await octokit.rest.repos.createOrUpdateFileContents({
      owner: OWNER,
      repo: REPO,
      path: input.path,
      branch,
      sha: input.sha,
      message: `docs(portal): update ${input.frontmatter.title}`,
      content: toBase64(renderMarkdown(input.frontmatter, input.body)),
    });
    const { data: pr } = await octokit.rest.pulls.create({
      owner: OWNER,
      repo: REPO,
      base: BASE_BRANCH,
      head: branch,
      title: `docs(portal): update ${input.frontmatter.title}`,
      body: `Edited via the portal authoring UI.\n\n- Path: \`${input.path}\``,
    });
    return { url: pr.html_url, number: pr.number };
  });
}

export async function deletePage(
  input: { path: string; sha: string; title: string }
): Promise<PullRequestResult> {
  const slug = input.path.split('/').pop()!.replace(/\.md$/, '');
  return withGitHub(async (octokit) => {
    const branch = `pages/delete-${slug}-${timestampSuffix()}`;
    await branchFromDefault(octokit, branch);
    await octokit.rest.repos.deleteFile({
      owner: OWNER,
      repo: REPO,
      path: input.path,
      branch,
      sha: input.sha,
      message: `docs(portal): remove ${input.title}`,
    });
    const { data: pr } = await octokit.rest.pulls.create({
      owner: OWNER,
      repo: REPO,
      base: BASE_BRANCH,
      head: branch,
      title: `docs(portal): remove ${input.title}`,
      body: `Deletion proposed via the portal authoring UI.\n\n- Path: \`${input.path}\``,
    });
    return { url: pr.html_url, number: pr.number };
  });
}
