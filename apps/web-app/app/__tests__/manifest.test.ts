import { describe, expect, it, beforeEach, afterEach } from 'vitest';

import manifest from '../manifest';

const envBackup = { ...process.env };

beforeEach(() => {
  process.env = { ...envBackup };
});

afterEach(() => {
  process.env = { ...envBackup };
});

describe('manifest route', () => {
  it('returns required PWA fields and icons with absolute URLs', () => {
    process.env.APP_PUBLIC_URL = 'https://example.com';

    const result = manifest();

    expect(result.name).toMatch(/Agent(?:s)?(?: SaaS)? Starter/);
    expect(result.start_url).toBe('/');
    expect(result.icons?.length).toBeGreaterThanOrEqual(2);
    result.icons?.forEach((icon) => {
      expect(icon.src.startsWith('https://example.com/')).toBe(true);
      expect(icon.type).toBe('image/png');
    });
  });
});
