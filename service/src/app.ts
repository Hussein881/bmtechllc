import { createPageSchema, assertSafeMarkdown, renderMarkdown, slugify, type CreatePageInput } from './contract.js';
export interface Identity { subject: string; email?: string; }
export interface GitHubWriter { fileExists(path: string): Promise<boolean>; getDefaultBranchSha(): Promise<string>; createBranch(branch: string, sha: string): Promise<void>; createFile(branch: string, path: string, content: string, message: string): Promise<void>; createPullRequest(branch: string, title: string, body: string): Promise<{ number: number; htmlUrl: string }>; }
export interface Dependencies { authenticate(request: Request): Promise<Identity | null>; writer: GitHubWriter; allowedOrigin: string; now?: () => Date; audit?: (event: Record<string, unknown>) => void; }
function json(value: unknown, status = 200, origin?: string): Response {
  const headers = new Headers({ 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' });
  // The portal deliberately sends credentialed requests. Reflect only the one
  // configured origin—never `*`—and vary cached responses by Origin.
  if (origin) {
    headers.set('access-control-allow-origin', origin);
    headers.set('access-control-allow-credentials', 'true');
    headers.set('vary', 'Origin');
  }
  return new Response(JSON.stringify(value), { status, headers });
}
function cors(request: Request, allowedOrigin: string): string | undefined { const origin = request.headers.get('origin'); return origin === allowedOrigin ? origin : undefined; }
export function createApp(deps: Dependencies) {
  return async (request: Request): Promise<Response> => {
    const origin = cors(request, deps.allowedOrigin);
    if (request.method === 'OPTIONS') { if (!origin) return json({ error: 'Origin is not allowed.' }, 403); return new Response(null, { status: 204, headers: { 'access-control-allow-origin': origin, 'access-control-allow-credentials': 'true', 'access-control-allow-methods': 'POST, OPTIONS', 'access-control-allow-headers': 'content-type, authorization', 'access-control-max-age': '600', vary: 'Origin' } }); }
    if (!origin && request.headers.has('origin')) return json({ error: 'Origin is not allowed.' }, 403);
    if (request.method !== 'POST') return json({ error: 'Method not allowed.' }, 405, origin);
    const identity = await deps.authenticate(request); if (!identity) return json({ error: 'Authentication required.' }, 401, origin);
    let body: unknown; try { body = await request.json(); } catch { return json({ error: 'Body must be valid JSON.' }, 400, origin); }
    const parsed = createPageSchema.safeParse(body); if (!parsed.success) return json({ error: 'Invalid page metadata.', details: parsed.error.flatten() }, 400, origin);
    try { return await createPage(parsed.data, identity, deps, origin); } catch (error) { const message = error instanceof Error ? error.message : 'Unable to create page.'; const clientError = /safe page slug|Raw HTML|too large/.test(message); return json({ error: clientError ? message : 'Unable to create page.' }, clientError ? 400 : 502, origin); }
  };
}
async function createPage(input: CreatePageInput, identity: Identity, deps: Dependencies, origin?: string): Promise<Response> {
  assertSafeMarkdown(input.body); const slug = slugify(input.title); const path = `portal/content/${input.section}/${slug}.md`;
  if (await deps.writer.fileExists(path)) return json({ error: 'A page with this title already exists in that section.' }, 409, origin);
  const timestamp = (deps.now ?? (() => new Date()))().toISOString().replace(/[-:.TZ]/g, '').slice(0, 14); const branch = `pages/${input.section}-${slug}-${timestamp}`;
  await deps.writer.createBranch(branch, await deps.writer.getDefaultBranchSha()); await deps.writer.createFile(branch, path, renderMarkdown(input), `docs(portal): add ${input.title}`);
  const pr = await deps.writer.createPullRequest(branch, `docs(portal): add ${input.title}`, `Created by ${identity.email ?? identity.subject} through the authenticated portal authoring flow.\n\n- Section: ${input.section}\n- Proposed path: \`${path}\`\n- Status: ${input.status}`);
  deps.audit?.({ action: 'page_submission_created', subject: identity.subject, section: input.section, slug, pullRequest: pr.number }); return json({ pullRequestNumber: pr.number, pullRequestUrl: pr.htmlUrl }, 201, origin);
}
