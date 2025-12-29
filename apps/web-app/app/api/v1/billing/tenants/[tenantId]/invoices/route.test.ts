import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { SubscriptionInvoiceListResponse } from '@/lib/api/client/types.gen';
import type { NextRequest } from 'next/server';

const listTenantInvoices = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/billing', () => ({
  listTenantInvoices,
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
  delete process.env.NEXT_PUBLIC_ENABLE_BILLING;
  listTenantInvoices.mockReset();
});

describe('GET /api/v1/billing/tenants/[tenantId]/invoices', () => {
  it('returns 404 when billing is disabled', async () => {
    process.env.NEXT_PUBLIC_ENABLE_BILLING = 'false';
    const { GET } = await loadHandler();

    const response = await GET(
      mockRequest('http://localhost/api/v1/billing/tenants/t1/invoices'),
      context('t1'),
    );

    expect(response.status).toBe(404);
  });

  it('rejects invalid offset', async () => {
    process.env.NEXT_PUBLIC_ENABLE_BILLING = 'true';
    const { GET } = await loadHandler();

    const response = await GET(
      mockRequest('http://localhost/api/v1/billing/tenants/t1/invoices?offset=-1'),
      context('t1'),
    );

    expect(response.status).toBe(400);
  });

  it('returns invoice list payload', async () => {
    process.env.NEXT_PUBLIC_ENABLE_BILLING = 'true';
    const { GET } = await loadHandler();

    const payload: SubscriptionInvoiceListResponse = {
      items: [
        {
          invoice_id: 'in_123',
          status: 'paid',
          amount_cents: 1200,
          currency: 'USD',
          period_start: '2025-01-01T00:00:00Z',
          period_end: '2025-02-01T00:00:00Z',
          hosted_invoice_url: 'https://example.com/invoices/in_123',
          created_at: '2025-01-01T00:00:00Z',
        },
      ],
      next_offset: null,
    };

    listTenantInvoices.mockResolvedValueOnce(payload);

    const request = mockRequest(
      'http://localhost/api/v1/billing/tenants/t1/invoices?limit=20&offset=0',
      new Headers({ 'x-tenant-role': 'viewer' }),
    );
    const response = await GET(request, context('t1'));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(payload);
    expect(listTenantInvoices).toHaveBeenCalledWith('t1', {
      limit: 20,
      offset: 0,
      tenantRole: 'viewer',
    });
  });
});
