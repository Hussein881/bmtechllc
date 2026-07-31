import { createApp, type GitHubWriter, type Identity } from './app.js';
import { createAppAuth } from '@octokit/auth-app';
import { Octokit } from '@octokit/rest';
import { createRemoteJWKSet, jwtVerify } from 'jose';

interface Env { ALLOWED_ORIGIN: string; GITHUB_APP_ID: string; GITHUB_APP_INSTALLATION_ID: string; GITHUB_APP_PRIVATE_KEY: string; GITHUB_OWNER: string; GITHUB_REPO: string; OIDC_ISSUER: string; OIDC_AUDIENCE: string; OIDC_JWKS_URL: string; OIDC_ALLOWED_SUBJECTS: string; }
function required(env: Record<string, string | undefined>, key: keyof Env): string { const value = env[key]; if (!value) throw new Error(`Missing required environment variable: ${key}`); return value; }
function environment(source: Record<string, string | undefined> = process.env): Env { return Object.fromEntries(['ALLOWED_ORIGIN', 'GITHUB_APP_ID', 'GITHUB_APP_INSTALLATION_ID', 'GITHUB_APP_PRIVATE_KEY', 'GITHUB_OWNER', 'GITHUB_REPO', 'OIDC_ISSUER', 'OIDC_AUDIENCE', 'OIDC_JWKS_URL', 'OIDC_ALLOWED_SUBJECTS'].map((key) => [key, required(source, key as keyof Env)])) as unknown as Env; }
export function allowedSubjects(value: string): Set<string> { const subjects = new Set(value.split(',').map((subject) => subject.trim()).filter(Boolean)); if (subjects.size === 0 || subjects.has('*')) throw new Error('OIDC_ALLOWED_SUBJECTS must list one or more explicit subject IDs.'); return subjects; }
function githubWriter(env: Env): GitHubWriter {
  const octokit = new Octokit({ authStrategy: createAppAuth, auth: { appId: env.GITHUB_APP_ID, installationId: env.GITHUB_APP_INSTALLATION_ID, privateKey: env.GITHUB_APP_PRIVATE_KEY.replace(/\\n/g, '\n') } }); const repo = { owner: env.GITHUB_OWNER, repo: env.GITHUB_REPO };
  return {
    async fileExists(path) { try { await octokit.rest.repos.getContent({ ...repo, path }); return true; } catch (error: unknown) { if ((error as { status?: number }).status === 404) return false; throw error; } },
    async getDefaultBranchSha() { const repository = await octokit.rest.repos.get(repo); const branch = await octokit.rest.repos.getBranch({ ...repo, branch: repository.data.default_branch }); return branch.data.commit.sha; },
    async createBranch(branch, sha) { await octokit.rest.git.createRef({ ...repo, ref: `refs/heads/${branch}`, sha }); },
    async createFile(branch, path, content, message) { await octokit.rest.repos.createOrUpdateFileContents({ ...repo, branch, path, message, content: Buffer.from(content).toString('base64') }); },
    async createPullRequest(head, title, body) { const pr = await octokit.rest.pulls.create({ ...repo, head, base: 'main', title, body }); return { number: pr.data.number, htmlUrl: pr.data.html_url }; },
  };
}
export function createProductionApp(env = environment()) {
  const jwks = createRemoteJWKSet(new URL(env.OIDC_JWKS_URL));
  const subjects = allowedSubjects(env.OIDC_ALLOWED_SUBJECTS);
  const authenticate = async (request: Request): Promise<Identity | null> => { const token = request.headers.get('authorization')?.match(/^Bearer (.+)$/i)?.[1]; if (!token) return null; try { const { payload } = await jwtVerify(token, jwks, { issuer: env.OIDC_ISSUER, audience: env.OIDC_AUDIENCE }); return typeof payload.sub === 'string' && subjects.has(payload.sub) ? { subject: payload.sub, email: typeof payload.email === 'string' ? payload.email : undefined } : null; } catch { return null; } };
  return createApp({ authenticate, writer: githubWriter(env), allowedOrigin: env.ALLOWED_ORIGIN, audit: (event) => console.info(JSON.stringify(event)) });
}
/** Deployment adapters (Cloudflare Workers, Vercel Edge) can call this fetch handler. */
export default { fetch: (request: Request) => createProductionApp()(request) };
