#!/usr/bin/env node
/**
 * CI gate for the internal knowledge base.
 *
 * What changed from the public-site version and why:
 *   - Dropped the confidentiality leak check. There is no public build to leak
 *     into; every page is internal by definition.
 *   - Dropped llms.txt / sitemap artifact checks. Those served external
 *     crawlers, which do not exist here.
 *   - Added an ownership check. Internal docs rot silently because no external
 *     pressure exists, so accountability is enforced at build time.
 *
 * Run after `astro build`. Exits non-zero on any failure.
 */
import { readFileSync, existsSync, readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';

const ROOT = new URL('../', import.meta.url).pathname;
const DIST = join(ROOT, 'dist');
const CONTENT = join(ROOT, 'content');
const BASE = '/bmtechllc/portal';

const failures = [];
const warnings = [];

function walk(dir, out = []) {
  if (!existsSync(dir)) return out;
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
  const source = relative(DIST, file);

  for (const match of html.matchAll(/href="([^"]+)"/g)) {
    const href = match[1];
    if (/^(https?:|mailto:|#|data:)/.test(href)) continue;
    if (/\.(css|js|xml|png|svg|jpg|ico|webmanifest)$/.test(href)) continue;

    linkCount++;
    const clean = href.split('#')[0].split('?')[0];
    if (!clean) continue;

    const withSlash = clean.endsWith('/') ? clean : clean + '/';
    if (
      !validPaths.has(clean) &&
      !validPaths.has(withSlash) &&
      !validPaths.has(withSlash + 'index.html') &&
      !existsSync(join(DIST, clean.replace(BASE, '')))
    ) {
      fail(`Broken internal link "${href}" in ${source}`);
    }
  }
}

// ── 2. Redirect destinations resolve ─────────────────────────────────────────
const { redirects } = JSON.parse(readFileSync(join(ROOT, 'redirects.json'), 'utf8'));
for (const [from, to] of Object.entries(redirects)) {
  const target = to.endsWith('/') ? to : to + '/';
  if (!validPaths.has(BASE + target)) {
    fail(`Redirect "${from}" points at "${to}", which does not resolve to a built page.`);
  }
}

// ── 3. index.json is valid and complete ──────────────────────────────────────
let index = [];
const indexPath = join(DIST, 'index.json');
if (!existsSync(indexPath)) {
  fail('Missing /index.json — internal tooling depends on it.');
} else {
  try {
    index = JSON.parse(readFileSync(indexPath, 'utf8'));
    if (!Array.isArray(index)) fail('index.json is not an array');
    for (const entry of index) {
      for (const field of ['url', 'title', 'description', 'section', 'updated', 'owner', 'status']) {
        if (entry[field] === undefined || entry[field] === '') {
          fail(`index.json entry missing "${field}": ${entry.url ?? '?'}`);
        }
      }
    }
  } catch (err) {
    fail(`index.json does not parse: ${err.message}`);
  }
}

// ── 4. Ownership + staleness ─────────────────────────────────────────────────
// Internal docs rot silently. Missing ownership fails; overdue review warns.
const KNOWN_OWNERS = new Set(['ah', 'kv', 'fa', 'team']);
const stale = [];

for (const file of walk(CONTENT).filter((f) => f.endsWith('.md'))) {
  const rel = relative(CONTENT, file);
  const fm = readFileSync(file, 'utf8').match(/^---\n([\s\S]*?)\n---/);
  if (!fm) {
    fail(`${rel} has no frontmatter`);
    continue;
  }

  const owner = fm[1].match(/^owner:\s*(\S+)/m)?.[1];
  const status = fm[1].match(/^status:\s*(\S+)/m)?.[1] ?? 'draft';
  const updated = fm[1].match(/^updated:\s*(\S+)/m)?.[1];
  const cycle = Number(fm[1].match(/^reviewCycleMonths:\s*(\d+)/m)?.[1] ?? 6);

  if (!owner) fail(`${rel} has no owner`);
  else if (!KNOWN_OWNERS.has(owner)) {
    fail(`${rel} has unknown owner "${owner}" — add them to KNOWN_OWNERS or fix the typo.`);
  }

  if (updated && status !== 'archived') {
    const months =
      (Date.now() - new Date(updated).getTime()) / (1000 * 60 * 60 * 24 * 30.44);
    if (months >= cycle) {
      stale.push({ rel, owner, months: Math.floor(months), cycle });
    }
  }
}

for (const s of stale) {
  warnings.push(`${s.rel} — ${s.months}mo old, ${s.cycle}mo cycle, owned by ${s.owner}`);
}

function fail(msg) {
  failures.push(msg);
}

// ── Report ───────────────────────────────────────────────────────────────────
console.log(
  `\nChecked ${htmlFiles.length} pages, ${linkCount} internal links, ` +
    `${Object.keys(redirects).length} redirects, ${index.length} indexed entries.`
);

if (warnings.length) {
  console.log(`\n⚠ ${warnings.length} page(s) overdue for review:\n`);
  for (const w of warnings) console.log(`  - ${w}`);
}

if (failures.length) {
  console.error(`\n✗ ${failures.length} failure(s):\n`);
  for (const f of failures) console.error(`  - ${f}`);
  process.exit(1);
}

console.log('\n✓ All checks passed.\n');
