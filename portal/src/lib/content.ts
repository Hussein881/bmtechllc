import { getCollection, type CollectionEntry } from 'astro:content';

export const SECTIONS = [
  'services',
  'methodology',
  'playbooks',
  'reference',
  'insights',
  'about',
] as const;

export type SectionName = typeof SECTIONS[number];

export const SECTION_LABELS: Record<SectionName, string> = {
  services: 'Services',
  methodology: 'Methodology',
  playbooks: 'Playbooks',
  reference: 'Reference',
  insights: 'Insights',
  about: 'About',
};

/** Docs-mode sections get sidebar + ToC. Browse-mode sections get editorial layout. */
export const DOCS_SECTIONS: SectionName[] = ['methodology', 'playbooks', 'reference'];

export interface PageRecord {
  section: SectionName;
  /** Collection entry id, e.g. "discovery/stakeholder-interviews" or "index" */
  id: string;
  /** URL path without base, e.g. "/playbooks/discovery/stakeholder-interviews/" */
  path: string;
  title: string;
  description: string;
  tags: string[];
  updated: Date;
  owner: string;
  order: number;
  related: string[];
  isIndex: boolean;
  /** Path segments below the section, e.g. ["discovery", "stakeholder-interviews"] */
  segments: string[];
  entry: CollectionEntry<SectionName>;
}

/** Strip trailing slash from BASE_URL for safe concatenation. */
export const base = import.meta.env.BASE_URL.replace(/\/$/, '');

/** Prefix a site-root path with the deployment base. */
export function withBase(path: string): string {
  const normalized = path.startsWith('/') ? path : `/${path}`;
  return `${base}${normalized}`;
}

/**
 * Load every published + public page across all collections into a flat,
 * sorted record list. This is the single source of truth for navigation,
 * search artifacts, and the LLM index.
 */
export async function getAllPages(): Promise<PageRecord[]> {
  const records: PageRecord[] = [];

  for (const section of SECTIONS) {
    const entries = await getCollection(section, ({ data }) =>
      data.status === 'published' && data.audience === 'public'
    );

    for (const entry of entries) {
      const isIndex = entry.id === 'index' || entry.id.endsWith('/index');
      const trimmedId = isIndex ? entry.id.replace(/\/?index$/, '') : entry.id;
      const segments = trimmedId ? trimmedId.split('/') : [];
      const path = segments.length
        ? `/${section}/${segments.join('/')}/`
        : `/${section}/`;

      records.push({
        section,
        id: entry.id,
        path,
        title: entry.data.title,
        description: entry.data.description,
        tags: entry.data.tags,
        updated: entry.data.updated,
        owner: entry.data.owner,
        order: entry.data.order,
        related: entry.data.related,
        isIndex,
        segments,
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
  children: NavNode[];
}

/**
 * Build a nested navigation tree for one section from its page paths.
 * Folder structure determines hierarchy; `order` frontmatter determines sequence.
 * No hand-maintained nav config exists — adding a file adds a nav entry.
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

    // Leaf node for the page itself
    level.push({
      label: page.title,
      path: page.path,
      order: page.order,
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

  // Intermediate folders (not the leaf itself)
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
