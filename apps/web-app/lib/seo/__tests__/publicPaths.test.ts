import { describe, expect, it } from 'vitest';

import { getPriorityForPath, getPublicPaths } from '../publicPaths';

describe('getPublicPaths', () => {
  it('returns root first and sorts remaining paths stably', () => {
    const paths = getPublicPaths();

    expect(paths[0]).toBe('/');
    const sortedCopy = ['/', ...paths.slice(1).slice().sort()];
    expect(paths).toEqual(sortedCopy);
  });

  it('deduplicates overlapping nav + static entries', () => {
    const paths = getPublicPaths();

    const pricingCount = paths.filter((p) => p === '/pricing').length;
    expect(pricingCount).toBe(1);
  });

  it('excludes external links from marketing nav', () => {
    const paths = getPublicPaths();

    const hasExternal = paths.some((p) => p.startsWith('http'));
    expect(hasExternal).toBe(false);
  });

  it('filters disallowed/app-only routes', () => {
    const paths = getPublicPaths();

    expect(paths).not.toContain('/login');
    expect(paths).not.toContain('/register');
    expect(paths).not.toContain('/chat');
    expect(paths).not.toContain('/billing');
    expect(paths).not.toContain('/account/security');
  });

  it('strips fragments and queries from paths', () => {
    const paths = getPublicPaths();

    expect(paths.some((p) => p.includes('#'))).toBe(false);
    expect(paths.some((p) => p.includes('?'))).toBe(false);
    expect(paths).toContain('/docs'); // /docs#agents should normalize here
  });
});

describe('getPriorityForPath', () => {
  it('assigns higher priority for key marketing pages', () => {
    expect(getPriorityForPath('/')).toBe(1);
    expect(getPriorityForPath('/pricing')).toBe(0.8);
    expect(getPriorityForPath('/docs')).toBe(0.8);
    expect(getPriorityForPath('/something-else')).toBe(0.6);
  });
});
