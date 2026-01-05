import { beforeEach, describe, expect, it, vi } from 'vitest';

const listBillingPlans = vi.hoisted(() => vi.fn());
const requireBillingFeature = vi.hoisted(() => vi.fn());

class FeatureFlagsApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = 'FeatureFlagsApiError';
  }
}

vi.mock('@/lib/server/services/billing', () => ({
  listBillingPlans,
}));
vi.mock('@/lib/server/features', () => ({
  FeatureFlagsApiError,
  requireBillingFeature,
}));

async function loadHandler() {
  // Re-import the module after adjusting feature flags.
  vi.resetModules();
  return import('./route');
}

beforeEach(() => {
  listBillingPlans.mockReset();
  requireBillingFeature.mockReset();
});

describe('GET /api/billing/plans', () => {
  it('returns 403 when billing is disabled', async () => {
    requireBillingFeature.mockRejectedValueOnce(
      new FeatureFlagsApiError(403, 'Billing is disabled.'),
    );
    const { GET } = await loadHandler();

    const response = await GET();

    expect(response.status).toBe(403);
  });

  it('returns plans when billing is enabled', async () => {
    requireBillingFeature.mockResolvedValueOnce(undefined);
    const { GET } = await loadHandler();
    listBillingPlans.mockResolvedValueOnce([{ code: 'starter' }]);

    const response = await GET();

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({ success: true, plans: [{ code: 'starter' }] });
    expect(listBillingPlans).toHaveBeenCalledTimes(1);
  });
});
