import { describe, expect, it, beforeEach, afterEach } from 'vitest';

import robots from '../robots';

const envBackup = { ...process.env };

beforeEach(() => {
  process.env = { ...envBackup };
});

afterEach(() => {
  process.env = { ...envBackup };
});

describe('robots route', () => {
  it('builds sitemap and host from APP_PUBLIC_URL', () => {
    process.env.APP_PUBLIC_URL = 'https://example.com';

    const result = robots();

    expect(result.host).toBe('https://example.com');
    expect(result.sitemap).toEqual(['https://example.com/sitemap.xml']);
  });

  it('disallows sensitive app and api routes', () => {
    process.env.APP_PUBLIC_URL = 'https://example.com';

    const result = robots();
    const rule = Array.isArray(result.rules) ? result.rules[0] : result.rules;

    expect(rule?.disallow).toContain('/api');
    expect(rule?.disallow).toContain('/account');
    expect(rule?.allow).toBe('/');
  });
});
