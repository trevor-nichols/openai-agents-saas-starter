import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { UsageTotalResponse } from '@/lib/api/client/types.gen';
import type { NextRequest } from 'next/server';

const listTenantUsageTotals = vi.hoisted(() => vi.fn());
const isBillingEnabled = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/billing', () => ({
  listTenantUsageTotals,
}));
vi.mock('@/lib/server/features', () => ({
  isBillingEnabled,
}));

async function loadHandler() {
  vi.resetModules();
  return import('./route');
}

const mockRequest = (url: string, headers?: Headers): NextRequest =>
  ({
    url,
    headers: headers ?? new Headers(),
  }) as unknown as NextRequest;

const context = (tenantId?: string): Parameters<
  (typeof import('./route'))['GET']
>[1] => ({
  params: Promise.resolve({ tenantId }),
});

beforeEach(() => {
  listTenantUsageTotals.mockReset();
  isBillingEnabled.mockReset();
});

describe('GET /api/v1/billing/tenants/[tenantId]/usage-totals', () => {
  it('returns 404 when billing is disabled', async () => {
    isBillingEnabled.mockResolvedValueOnce(false);
    const { GET } = await loadHandler();

    const response = await GET(mockRequest('http://localhost/api/v1/billing/tenants/t1/usage-totals'), context('t1'));

    expect(response.status).toBe(404);
  });

  it('returns usage totals payload', async () => {
    isBillingEnabled.mockResolvedValueOnce(true);
    const { GET } = await loadHandler();

    const totals: UsageTotalResponse[] = [
      {
        feature_key: 'tokens',
        unit: 'tokens',
        quantity: 4200,
        window_start: '2025-01-01T00:00:00Z',
        window_end: '2025-02-01T00:00:00Z',
      },
    ];

    listTenantUsageTotals.mockResolvedValueOnce(totals);

    const request = mockRequest(
      'http://localhost/api/v1/billing/tenants/t1/usage-totals?feature_keys=tokens&period_start=2025-01-01T00:00:00Z&period_end=2025-02-01T00:00:00Z',
      new Headers({ 'x-tenant-role': 'viewer' }),
    );
    const response = await GET(request, context('t1'));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(totals);
    expect(listTenantUsageTotals).toHaveBeenCalledWith('t1', {
      featureKeys: ['tokens'],
      periodStart: '2025-01-01T00:00:00Z',
      periodEnd: '2025-02-01T00:00:00Z',
      tenantRole: 'viewer',
    });
  });
});
