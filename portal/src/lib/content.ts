import { getCollection, type CollectionEntry } from 'astro:content';
import { SECTIONS } from './page-contract';
export { SECTIONS } from './page-contract';

export type SectionName = typeof SECTIONS[number];

export const SECTION_LABELS: Record<SectionName, string> = {
  guide: 'Guide',
  onboarding: 'Onboarding',
  methodology: 'Methodology',
  playbooks: 'Playbooks',
  runbooks: 'Runbooks',
  reference: 'Reference',
};

/**
 * One-line purpose per section, shown on the home grid and section indexes.
 *
 * These are the main signal for "does my content belong here", so each names
 * the *kind* of writing rather than the topic: reference explains, playbooks
 * advise, runbooks instruct, guide covers this site itself.
 */
export const SECTION_BLURBS: Record<SectionName, string> = {
  guide: 'How this knowledge base works — using it, adding to it, keeping it useful.',
  onboarding: 'What to read first, and in what order, when you are new here.',
  methodology: 'How we work and why we work that way.',
  playbooks: 'Advice for work that takes judgment — if the answer is "it depends", it belongs here.',
  runbooks: 'Exact steps for something that should go the same way every time.',
  reference: 'Things you look up — notes, definitions, and what we learned about a topic.',
};

/**
 * Every section is docs-mode. There is no marketing surface in an internal
 * KB — sidebar and on-page ToC are always useful.
 */
export type PageStatus = 'draft' | 'published' | 'archived';
export type Visibility = 'internal' | 'shareable';

export interface PageRecord {
  section: SectionName;
  /** Collection entry id, e.g. "discovery/stakeholder-interviews" or "index" */
  id: string;
  /** URL path without base, e.g. "/playbooks/discovery/stakeholder-interviews/" */
  path: string;
  title: string;
  description: string;
  tags: string[];
  status: PageStatus;
  visibility: Visibility;
  updated: Date;
  owner: string;
  reviewCycleMonths: number;
  order: number;
  related: string[];
  isIndex: boolean;
  /** Path segments below the section, e.g. ["discovery", "stakeholder-interviews"] */
  segments: string[];
  /** True once `updated` is older than `reviewCycleMonths`. */
  isStale: boolean;
  /** Whole months since last update. */
  monthsSinceUpdate: number;
  entry: CollectionEntry<SectionName>;
}

/** Strip trailing slash from BASE_URL for safe concatenation. */
export const base = import.meta.env.BASE_URL.replace(/\/$/, '');

/** Prefix a site-root path with the deployment base. */
export function withBase(path: string): string {
  const normalized = path.startsWith('/') ? path : `/${path}`;
  return `${base}${normalized}`;
}

export function monthsSince(date: Date, now = new Date()): number {
  return Math.max(
    0,
    (now.getFullYear() - date.getFullYear()) * 12 + (now.getMonth() - date.getMonth())
  );
}

/**
 * Load every page across all collections into a flat, sorted record list.
 * This is the single source of truth for navigation, search, and the
 * machine-readable index.
 *
 * Unlike a public site, nothing is filtered out here — drafts and archived
 * pages render with a banner. The team needs to see work in progress.
 */
export async function getAllPages(): Promise<PageRecord[]> {
  const records: PageRecord[] = [];
  const now = new Date();

  for (const section of SECTIONS) {
    const entries = await getCollection(section);

    for (const entry of entries) {
      const isIndex = entry.id === 'index' || entry.id.endsWith('/index');
      const trimmedId = isIndex ? entry.id.replace(/\/?index$/, '') : entry.id;
      const segments = trimmedId ? trimmedId.split('/') : [];
      const path = segments.length
        ? `/${section}/${segments.join('/')}/`
        : `/${section}/`;

      const age = monthsSince(entry.data.updated, now);

      records.push({
        section,
        id: entry.id,
        path,
        title: entry.data.title,
        description: entry.data.description,
        tags: entry.data.tags,
        status: entry.data.status,
        visibility: entry.data.visibility,
        updated: entry.data.updated,
        owner: entry.data.owner,
        reviewCycleMonths: entry.data.reviewCycleMonths,
        order: entry.data.order,
        related: entry.data.related,
        isIndex,
        segments,
        isStale: entry.data.status !== 'archived' && age >= entry.data.reviewCycleMonths,
        monthsSinceUpdate: age,
        entry,
      });
    }
  }

  return records.sort(
    (a, b) => a.order - b.order || a.title.localeCompare(b.title)
  );
}

export interface NavNode {
  label: string;
  path?: string;
  order: number;
  status?: PageStatus;
  children: NavNode[];
}

/**
 * Build a nested navigation tree for one section from its page paths.
 * Folder structure determines hierarchy; `order` frontmatter determines
 * sequence. No hand-maintained nav config exists — adding a file adds a
 * nav entry.
 */
export function buildSectionTree(pages: PageRecord[], section: SectionName): NavNode[] {
  const sectionPages = pages.filter((p) => p.section === section && !p.isIndex);
  const roots: NavNode[] = [];

  for (const page of sectionPages) {
    let level = roots;

    // Walk/create intermediate folder nodes
    for (let i = 0; i < page.segments.length - 1; i++) {
      const label = humanize(page.segments[i]!);
      let node = level.find((n) => n.label === label);
      if (!node) {
        node = { label, order: 999, children: [] };
        level.push(node);
      }
      level = node.children;
    }

    level.push({
      label: page.title,
      path: page.path,
      order: page.order,
      status: page.status,
      children: [],
    });
  }

  sortTree(roots);
  return roots;
}

function sortTree(nodes: NavNode[]): void {
  nodes.sort((a, b) => a.order - b.order || a.label.localeCompare(b.label));
  for (const node of nodes) sortTree(node.children);
}

/** "case-studies" -> "Case Studies" */
export function humanize(slug: string): string {
  return slug
    .split('-')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export interface Crumb {
  label: string;
  path?: string;
}

/** Build breadcrumb trail mirroring the folder path. */
export function buildBreadcrumbs(page: PageRecord): Crumb[] {
  const crumbs: Crumb[] = [{ label: 'Home', path: '/' }];

  crumbs.push({
    label: SECTION_LABELS[page.section],
    path: `/${page.section}/`,
  });

  for (let i = 0; i < page.segments.length - 1; i++) {
    crumbs.push({ label: humanize(page.segments[i]!) });
  }

  if (!page.isIndex) {
    crumbs.push({ label: page.title });
  }

  return crumbs;
}

/**
 * Resolve a `related:` frontmatter slug to a real page.
 * Accepts a bare slug ("engagement-model") or a full path fragment.
 */
export function resolveRelated(pages: PageRecord[], slug: string): PageRecord | undefined {
  const needle = slug.replace(/^\/|\/$/g, '');
  return pages.find(
    (p) =>
      p.segments.join('/') === needle ||
      p.segments.at(-1) === needle ||
      p.path.replace(/^\/|\/$/g, '') === needle
  );
}

/** Pages that link *to* the given page, derived from `related` edges. */
export function findBacklinks(pages: PageRecord[], target: PageRecord): PageRecord[] {
  return pages.filter(
    (p) =>
      p.path !== target.path &&
      p.related.some((slug) => resolveRelated(pages, slug)?.path === target.path)
  );
}

/**
 * Every page that would be left with a dangling reference if `target` were
 * deleted — both `related:` edges and inline body links.
 *
 * This is broader than findBacklinks on purpose: the build gate fails on any
 * broken internal link, including ones written inline in prose, which the
 * `related`-only view misses. Used to warn before proposing a deletion, since
 * otherwise the problem only surfaces as a red CI run on the resulting PR.
 */
export function findInboundReferences(pages: PageRecord[], target: PageRecord): PageRecord[] {
  const withoutBase = target.path;
  const withBasePath = `${base}${target.path}`;
  // Trailing slash is optional in authored links, so match the path stem and
  // accept either form.
  const stems = [withoutBase, withBasePath].map((p) => p.replace(/\/$/, ''));

  return pages.filter((page) => {
    if (page.path === target.path) return false;
    if (page.related.some((slug) => resolveRelated(pages, slug)?.path === target.path)) return true;

    const body = page.entry.body ?? '';
    return stems.some((stem) => body.includes(`](${stem})`) || body.includes(`](${stem}/)`));
  });
}
