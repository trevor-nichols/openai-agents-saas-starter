import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { DEFAULT_FEATURE_FLAGS } from '@/lib/features/constants';

const getRequestOrigin = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/requestOrigin', () => ({
  getRequestOrigin,
}));

import { getFeatureFlags } from '../features';

let warnSpy: ReturnType<typeof vi.spyOn> | null = null;

beforeEach(() => {
  getRequestOrigin.mockReset();
  warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
});

afterEach(() => {
  if (warnSpy) {
    warnSpy.mockRestore();
    warnSpy = null;
  }
  vi.unstubAllGlobals();
});

describe('getFeatureFlags', () => {
  it('returns BFF feature flags when available', async () => {
    const payload = { billingEnabled: true, billingStreamEnabled: false };
    getRequestOrigin.mockResolvedValue('https://app.example.com');
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(payload), { status: 200 }),
    );
    vi.stubGlobal('fetch', fetchMock);

    const result = await getFeatureFlags();

    expect(getRequestOrigin).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith(
      'https://app.example.com/api/health/features',
      { cache: 'no-store' },
    );
    expect(result).toEqual(payload);
  });

  it('falls back to defaults when the BFF responds with an error', async () => {
    getRequestOrigin.mockResolvedValue('https://app.example.com');
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 502 }));
    vi.stubGlobal('fetch', fetchMock);

    const result = await getFeatureFlags();

    expect(result).toEqual(DEFAULT_FEATURE_FLAGS);
    expect(warnSpy).toHaveBeenCalled();
  });
});
