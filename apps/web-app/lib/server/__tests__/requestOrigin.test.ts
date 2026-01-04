import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const headersMock = vi.hoisted(() => vi.fn());

vi.mock('next/headers', () => ({
  headers: headersMock,
}));

import { getRequestOrigin } from '../requestOrigin';

const envBackup = { ...process.env };

beforeEach(() => {
  process.env = { ...envBackup };
  headersMock.mockReset();
});

afterEach(() => {
  process.env = { ...envBackup };
});

describe('getRequestOrigin', () => {
  it('uses forwarded host and proto when present', async () => {
    headersMock.mockResolvedValue(
      new Headers({
        'x-forwarded-host': 'example.com:8443',
        'x-forwarded-proto': 'https',
      }),
    );

    await expect(getRequestOrigin()).resolves.toBe('https://example.com:8443');
  });

  it('falls back to APP_PUBLIC_URL when headers are missing', async () => {
    process.env.APP_PUBLIC_URL = 'https://app.example.com';
    headersMock.mockResolvedValue(new Headers());

    await expect(getRequestOrigin()).resolves.toBe('https://app.example.com');
  });

  it('falls back to APP_PUBLIC_URL when headers throw', async () => {
    process.env.APP_PUBLIC_URL = 'https://app.example.com';
    headersMock.mockRejectedValue(new Error('boom'));

    await expect(getRequestOrigin()).resolves.toBe('https://app.example.com');
  });
});
