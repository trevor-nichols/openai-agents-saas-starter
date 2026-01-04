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
    delete process.env.APP_PUBLIC_URL;

    expect(getSiteUrl()).toBe('http://localhost:3000');
  });

  it('normalizes protocol/host and strips trailing slash', () => {
    process.env.APP_PUBLIC_URL = 'HTTPS://Example.COM:8443/';

    expect(getSiteUrl()).toBe('https://example.com:8443');
  });

  it('throws when a path segment is present', () => {
    process.env.APP_PUBLIC_URL = 'https://example.com/app';

    expect(() => getSiteUrl()).toThrow();
  });
});

describe('buildAbsoluteUrl', () => {
  it('concatenates the base and normalized path', () => {
    process.env.APP_PUBLIC_URL = 'https://example.com/';

    expect(buildAbsoluteUrl('pricing')).toBe('https://example.com/pricing');
    expect(buildAbsoluteUrl('/pricing')).toBe('https://example.com/pricing');
  });
});
