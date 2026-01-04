import { beforeEach, describe, expect, it, vi } from 'vitest';

const listBillingPlans = vi.hoisted(() => vi.fn());
const isBillingEnabled = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/billing', () => ({
  listBillingPlans,
}));
vi.mock('@/lib/server/features', () => ({
  isBillingEnabled,
}));

async function loadHandler() {
  // Re-import the module after adjusting feature flags.
  vi.resetModules();
  return import('./route');
}

beforeEach(() => {
  listBillingPlans.mockReset();
  isBillingEnabled.mockReset();
});

describe('GET /api/billing/plans', () => {
  it('returns 404 when billing is disabled', async () => {
    isBillingEnabled.mockResolvedValueOnce(false);
    const { GET } = await loadHandler();

    const response = await GET();

    expect(response.status).toBe(404);
  });

  it('returns plans when billing is enabled', async () => {
    isBillingEnabled.mockResolvedValueOnce(true);
    const { GET } = await loadHandler();
    listBillingPlans.mockResolvedValueOnce([{ code: 'starter' }]);

    const response = await GET();

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({ success: true, plans: [{ code: 'starter' }] });
    expect(listBillingPlans).toHaveBeenCalledTimes(1);
  });
});
