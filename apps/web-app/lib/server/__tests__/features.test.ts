import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { DEFAULT_FEATURE_FLAGS } from '@/lib/features/constants';

import * as features from '../features';

let warnSpy: ReturnType<typeof vi.spyOn>;
let backendSpy: ReturnType<typeof vi.spyOn>;

beforeEach(() => {
  warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
  backendSpy = vi.spyOn(features, 'getBackendFeatureFlags');
});

afterEach(() => {
  warnSpy.mockRestore();
  backendSpy.mockRestore();
  vi.unstubAllGlobals();
});

describe('getFeatureFlags', () => {
  it('returns backend feature flags when available', async () => {
    const payload = { billingEnabled: true, billingStreamEnabled: false };
    backendSpy.mockResolvedValueOnce(payload);

    const result = await features.getFeatureFlags();

    expect(backendSpy).toHaveBeenCalledTimes(1);
    expect(result).toEqual(payload);
  });

  it('falls back to defaults when the backend fetch fails', async () => {
    backendSpy.mockRejectedValueOnce(new Error('boom'));

    const result = await features.getFeatureFlags();

    expect(result).toEqual(DEFAULT_FEATURE_FLAGS);
    expect(warnSpy).toHaveBeenCalled();
  });
});
