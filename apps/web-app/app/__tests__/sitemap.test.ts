import { describe, expect, it, beforeEach, afterEach } from 'vitest';

import sitemap from '../sitemap';

const envBackup = { ...process.env };

beforeEach(() => {
  process.env = { ...envBackup };
});

afterEach(() => {
  process.env = { ...envBackup };
});

describe('sitemap route', () => {
  it('emits absolute URLs for public marketing paths', () => {
    process.env.APP_PUBLIC_URL = 'https://example.com';
    process.env.VERCEL_GIT_COMMIT_TIMESTAMP = '2024-01-01T00:00:00.000Z';

    const entries = sitemap();

    expect(entries.length).toBeGreaterThan(3);
    expect(entries.every((entry) => entry.url.startsWith('https://example.com/'))).toBe(true);
    expect(entries.find((entry) => entry.url === 'https://example.com/pricing')).toBeDefined();
    const [first] = entries;
    expect(first).toBeDefined();
    expect(first!.lastModified).toBeInstanceOf(Date);
  });
});
