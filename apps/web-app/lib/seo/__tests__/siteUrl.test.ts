import { describe, expect, it, beforeEach, afterEach } from 'vitest';

import { buildAbsoluteUrl, getSiteUrl } from '../siteUrl';

const envBackup = { ...process.env };

beforeEach(() => {
  process.env = { ...envBackup };
});

afterEach(() => {
  process.env = { ...envBackup };
});

describe('getSiteUrl', () => {
  it('returns fallback localhost when no env provided', () => {
    delete process.env.SITE_URL;
    delete process.env.NEXT_PUBLIC_SITE_URL;

    expect(getSiteUrl()).toBe('http://localhost:3000');
  });

  it('normalizes protocol/host and strips trailing slash', () => {
    process.env.SITE_URL = 'HTTPS://Example.COM:8443/';

    expect(getSiteUrl()).toBe('https://example.com:8443');
  });

  it('prefers SITE_URL over NEXT_PUBLIC_SITE_URL', () => {
    process.env.SITE_URL = 'https://primary.example';
    process.env.NEXT_PUBLIC_SITE_URL = 'https://secondary.example';

    expect(getSiteUrl()).toBe('https://primary.example');
  });

  it('throws when a path segment is present', () => {
    process.env.SITE_URL = 'https://example.com/app';

    expect(() => getSiteUrl()).toThrow();
  });
});

describe('buildAbsoluteUrl', () => {
  it('concatenates the base and normalized path', () => {
    process.env.SITE_URL = 'https://example.com/';

    expect(buildAbsoluteUrl('pricing')).toBe('https://example.com/pricing');
    expect(buildAbsoluteUrl('/pricing')).toBe('https://example.com/pricing');
  });
});
