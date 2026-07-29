#!/usr/bin/env node
/**
 * CI gate: validates the built site.
 *   1. Internal links resolve to a real page
 *   2. Machine artifacts exist and parse
 *   3. No internal/draft content leaked into any public artifact
 *
 * Run after `astro build`. Exits non-zero on any failure.
 */
import { readFileSync, existsSync, readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';

const DIST = new URL('../dist/', import.meta.url).pathname;
const BASE = '/bmtechllc/portal';
const failures = [];

function fail(msg) {
  failures.push(msg);
}

// ── Collect every built HTML file ────────────────────────────────────────────
function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) walk(full, out);
    else out.push(full);
  }
  return out;
}

if (!existsSync(DIST)) {
  console.error('✗ dist/ not found — run `npm run build:site` first.');
  process.exit(1);
}

const files = walk(DIST);
const htmlFiles = files.filter((f) => f.endsWith('.html'));

// Build the set of valid internal URLs from what actually got emitted
const validPaths = new Set();
for (const file of files) {
  const rel = '/' + relative(DIST, file).replace(/\\/g, '/');
  validPaths.add(BASE + rel);
  if (rel.endsWith('/index.html')) {
    validPaths.add(BASE + rel.replace(/index\.html$/, ''));
    validPaths.add(BASE + rel.replace(/\/index\.html$/, ''));
  }
}

// ── 1. Internal link check ───────────────────────────────────────────────────
let linkCount = 0;
for (const file of htmlFiles) {
  const html = readFileSync(file, 'utf8');
  const source = '/' + relative(DIST, file);

  for (const match of html.matchAll(/href="([^"]+)"/g)) {
    const href = match[1];

    // Skip external, anchors, mailto, and asset requests
    if (/^(https?:|mailto:|#|data:)/.test(href)) continue;
    if (/\.(css|js|xml|png|svg|jpg|ico|webmanifest)$/.test(href)) continue;

    linkCount++;
    const clean = href.split('#')[0].split('?')[0];
    if (!clean) continue;

    const withSlash = clean.endsWith('/') ? clean : clean + '/';
    const asIndex = withSlash + 'index.html';

    if (
      !validPaths.has(clean) &&
      !validPaths.has(withSlash) &&
      !validPaths.has(asIndex) &&
      !existsSync(join(DIST, clean.replace(BASE, '')))
    ) {
      fail(`Broken internal link "${href}" in ${source}`);
    }
  }
}

// ── 2. Machine artifacts ─────────────────────────────────────────────────────
const artifacts = ['llms.txt', 'llms-full.txt', 'index.json', 'sitemap-index.xml'];
for (const name of artifacts) {
  const path = join(DIST, name);
  if (!existsSync(path)) {
    fail(`Missing machine artifact: /${name}`);
    continue;
  }
  if (statSync(path).size === 0) fail(`Empty machine artifact: /${name}`);
}

let index = [];
const indexPath = join(DIST, 'index.json');
if (existsSync(indexPath)) {
  try {
    index = JSON.parse(readFileSync(indexPath, 'utf8'));
    if (!Array.isArray(index)) fail('index.json is not an array');
    for (const entry of index) {
      for (const field of ['url', 'title', 'description', 'section', 'updated']) {
        if (!entry[field]) fail(`index.json entry missing "${field}": ${entry.url ?? '?'}`);
      }
    }
  } catch (err) {
    fail(`index.json does not parse: ${err.message}`);
  }
}

// ── 3. Confidentiality leak check ────────────────────────────────────────────
// Any page marked internal/client or status draft must not appear anywhere.
const contentDir = new URL('../content/', import.meta.url).pathname;
const mdFiles = walk(contentDir).filter((f) => f.endsWith('.md'));

const excludedTitles = [];
for (const file of mdFiles) {
  const raw = readFileSync(file, 'utf8');
  const fm = raw.match(/^---\n([\s\S]*?)\n---/);
  if (!fm) continue;

  const audience = fm[1].match(/^audience:\s*(\S+)/m)?.[1];
  const status = fm[1].match(/^status:\s*(\S+)/m)?.[1];
  const title = fm[1].match(/^title:\s*(.+)$/m)?.[1]?.trim();

  if (audience !== 'public' || status !== 'published') {
    excludedTitles.push({ title, file: relative(contentDir, file) });
  }
}

const llms = existsSync(join(DIST, 'llms.txt')) ? readFileSync(join(DIST, 'llms.txt'), 'utf8') : '';
const llmsFull = existsSync(join(DIST, 'llms-full.txt'))
  ? readFileSync(join(DIST, 'llms-full.txt'), 'utf8')
  : '';

for (const { title, file } of excludedTitles) {
  if (!title) continue;
  if (llms.includes(title)) fail(`LEAK: non-public page "${title}" (${file}) appears in llms.txt`);
  if (llmsFull.includes(title)) fail(`LEAK: non-public page "${title}" (${file}) appears in llms-full.txt`);
  if (index.some((e) => e.title === title)) fail(`LEAK: non-public page "${title}" (${file}) appears in index.json`);
}

// ── Report ───────────────────────────────────────────────────────────────────
console.log(`\nChecked ${htmlFiles.length} pages, ${linkCount} internal links, ${artifacts.length} artifacts.`);
console.log(`Indexed pages: ${index.length}. Excluded (non-public): ${excludedTitles.length}.`);

if (failures.length) {
  console.error(`\n✗ ${failures.length} failure(s):\n`);
  for (const f of failures) console.error(`  - ${f}`);
  process.exit(1);
}

console.log('\n✓ All checks passed.\n');
