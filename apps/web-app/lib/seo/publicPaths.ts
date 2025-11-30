import {
  MARKETING_CTA_LINK,
  MARKETING_FOOTER_COLUMNS,
  MARKETING_PRIMARY_LINKS,
  MARKETING_SECONDARY_LINKS,
} from '@/app/(marketing)/_components/nav-links';
import { isPathDisallowed } from './disallowedPaths';

const STATIC_PATHS: string[] = [
  '/',
  '/features',
  '/pricing',
  '/docs',
  '/about',
  '/contact',
  '/privacy',
  '/terms',
  '/status',
  '/request-access',
];

const PRIORITY_MAP: Record<string, number> = {
  '/': 1,
  '/pricing': 0.8,
  '/docs': 0.8,
  '/features': 0.8,
};

const normalizePath = (path: string): string => {
  const trimmed = path.trim();
  const ensureLeadingSlash = trimmed.startsWith('/') ? trimmed : `/${trimmed}`;
  // Strip query/hash fragments to comply with sitemap <loc> requirements.
  const withoutSearch = ensureLeadingSlash.split('?')[0] ?? ensureLeadingSlash;
  const withoutHash = withoutSearch.split('#')[0] ?? withoutSearch;
  if (withoutHash === '/') return '/';
  return withoutHash.endsWith('/') ? withoutHash.slice(0, -1) : withoutHash;
};

type HasHref = { href: string };

const isInternal = (link: HasHref) => link.href.startsWith('/');

const flattenFooterLinks = () =>
  MARKETING_FOOTER_COLUMNS.flatMap((column) => column.links)
    .filter(isInternal)
    .map((link) => link.href);

const collectNavPaths = (): string[] => {
  const navLinks = [
    ...MARKETING_PRIMARY_LINKS,
    ...MARKETING_SECONDARY_LINKS,
    MARKETING_CTA_LINK,
  ];

  return navLinks.filter(isInternal).map((link) => link.href);
};

const dedupe = (paths: string[]): string[] => {
  const seen = new Set<string>();
  const ordered: string[] = [];
  for (const path of paths) {
    if (seen.has(path)) continue;
    seen.add(path);
    ordered.push(path);
  }
  return ordered;
};

const sortStable = (paths: string[]): string[] => {
  if (paths.length === 0) return paths;
  const root = paths.filter((p) => p === '/');
  const rest = paths.filter((p) => p !== '/').sort();
  return [...root, ...rest];
};

export const getPublicPaths = (): string[] => {
  const fromNav = collectNavPaths();
  const fromFooter = flattenFooterLinks();

  const all = [...STATIC_PATHS, ...fromNav, ...fromFooter]
    .map(normalizePath)
    .filter((path) => !isPathDisallowed(path));

  return sortStable(dedupe(all));
};

export const getPriorityForPath = (path: string): number => PRIORITY_MAP[path] ?? 0.6;
