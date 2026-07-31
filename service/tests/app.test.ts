import assert from 'node:assert/strict';
import test from 'node:test';
import { createApp, type GitHubWriter } from '../src/app.js';
import { renderMarkdown, slugify } from '../src/contract.js';
import { allowedSubjects } from '../src/index.js';
const input = { section: 'playbooks' as const, title: 'Secure Page Authoring', description: 'A safe, review-based workflow for creating internal documentation pages.', tags: ['security', 'process'] as ('security' | 'process')[], status: 'draft' as const, visibility: 'internal' as const, owner: 'ah', updated: new Date('2026-07-31'), reviewCycleMonths: 6, order: 50, related: ['glossary'], body: '# Secure page authoring\n\nUse a pull request.' };
test('slug and Markdown renderer create a safe portal file', () => { assert.equal(slugify('Secure Page Authoring!'), 'secure-page-authoring'); assert.match(renderMarkdown(input), /title: "Secure Page Authoring"/); assert.match(renderMarkdown(input), /updated: 2026-07-31/); });
test('authenticated submission creates a branch, file, and pull request', async () => {
  const calls: string[] = []; const writer: GitHubWriter = { fileExists: async () => false, getDefaultBranchSha: async () => 'abc', createBranch: async (branch) => { calls.push(`branch:${branch}`); }, createFile: async (_branch, path, content) => { calls.push(`file:${path}`); assert.match(content, /# Secure page authoring/); }, createPullRequest: async () => ({ number: 42, htmlUrl: 'https://github.example/pr/42' }) };
  const app = createApp({ authenticate: async () => ({ subject: 'user-1', email: 'author@example.com' }), writer, allowedOrigin: 'https://portal.example', now: () => new Date('2026-07-31T12:34:56Z') }); const response = await app(new Request('https://service.example/pages', { method: 'POST', headers: { origin: 'https://portal.example', 'content-type': 'application/json' }, body: JSON.stringify({ ...input, updated: '2026-07-31' }) }));
  assert.equal(response.status, 201); assert.equal(response.headers.get('access-control-allow-origin'), 'https://portal.example'); assert.equal(response.headers.get('access-control-allow-credentials'), 'true'); assert.equal(response.headers.get('vary'), 'Origin'); assert.deepEqual(await response.json(), { pullRequestNumber: 42, pullRequestUrl: 'https://github.example/pr/42' }); assert.equal(calls.length, 2); assert.match(calls[0]!, /^branch:pages\/playbooks-secure-page-authoring-20260731123456$/); assert.equal(calls[1], 'file:portal/content/playbooks/secure-page-authoring.md');
});
test('service rejects unauthenticated and raw HTML submissions', async () => {
  const writer = {} as GitHubWriter; const anonymous = createApp({ authenticate: async () => null, writer, allowedOrigin: 'https://portal.example' }); assert.equal((await anonymous(new Request('https://service.example', { method: 'POST', body: '{}' }))).status, 401);
  const app = createApp({ authenticate: async () => ({ subject: 'user-1' }), writer, allowedOrigin: 'https://portal.example' }); const invalid = await app(new Request('https://service.example', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ ...input, body: '<script>alert(1)</script>' }) })); assert.equal(invalid.status, 400); assert.match((await invalid.json() as { error: string }).error, /Raw HTML/);
});
test('production authorization requires an explicit OIDC subject allowlist', () => {
  assert.deepEqual([...allowedSubjects('issuer|person-a, issuer|person-b')], ['issuer|person-a', 'issuer|person-b']);
  assert.throws(() => allowedSubjects('*'), /explicit subject IDs/);
  assert.throws(() => allowedSubjects('  '), /explicit subject IDs/);
});
test('credentialed CORS preflight permits only the configured origin', async () => {
  const app = createApp({ authenticate: async () => null, writer: {} as GitHubWriter, allowedOrigin: 'https://portal.example' });
  const response = await app(new Request('https://service.example', { method: 'OPTIONS', headers: { origin: 'https://portal.example' } }));
  assert.equal(response.status, 204); assert.equal(response.headers.get('access-control-allow-origin'), 'https://portal.example'); assert.equal(response.headers.get('access-control-allow-credentials'), 'true'); assert.equal(response.headers.get('vary'), 'Origin');
  assert.equal((await app(new Request('https://service.example', { method: 'OPTIONS', headers: { origin: 'https://attacker.example' } }))).status, 403);
});
