import { beforeEach, describe, expect, it, vi } from 'vitest';

const listBillingPlans = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/billing', () => ({
  listBillingPlans,
}));

async function loadHandler() {
  // Re-import the module after adjusting env flags so billingEnabled is recomputed.
  vi.resetModules();
  return import('./route');
}

beforeEach(() => {
  delete process.env.NEXT_PUBLIC_ENABLE_BILLING;
  listBillingPlans.mockReset();
});

describe('GET /api/billing/plans', () => {
  it('returns 404 when billing is disabled', async () => {
    process.env.NEXT_PUBLIC_ENABLE_BILLING = 'false';
    const { GET } = await loadHandler();

    const response = await GET();

    expect(response.status).toBe(404);
  });

  it('returns plans when billing is enabled', async () => {
    process.env.NEXT_PUBLIC_ENABLE_BILLING = 'true';
    const { GET } = await loadHandler();
    listBillingPlans.mockResolvedValueOnce([{ code: 'starter' }]);

    const response = await GET();

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({ success: true, plans: [{ code: 'starter' }] });
    expect(listBillingPlans).toHaveBeenCalledTimes(1);
  });
});
