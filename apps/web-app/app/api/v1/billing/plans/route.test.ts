import { beforeEach, describe, expect, it, vi } from 'vitest';

const listBillingPlans = vi.hoisted(() => vi.fn());
vi.mock('@/lib/server/services/billing', () => ({
  listBillingPlans,
}));

async function loadHandler() {
  // Re-import the module after adjusting feature flags.
  vi.resetModules();
  return import('./route');
}

beforeEach(() => {
  listBillingPlans.mockReset();
});

describe('GET /api/billing/plans', () => {
  it('returns plans when billing is enabled', async () => {
    const { GET } = await loadHandler();
    listBillingPlans.mockResolvedValueOnce([{ code: 'starter' }]);

    const response = await GET();

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({ success: true, plans: [{ code: 'starter' }] });
    expect(listBillingPlans).toHaveBeenCalledTimes(1);
  });

  it('returns 500 when the service fails', async () => {
    const { GET } = await loadHandler();
    listBillingPlans.mockRejectedValueOnce(new Error('Boom'));

    const response = await GET();

    expect(response.status).toBe(500);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'Boom',
    });
  });
});
