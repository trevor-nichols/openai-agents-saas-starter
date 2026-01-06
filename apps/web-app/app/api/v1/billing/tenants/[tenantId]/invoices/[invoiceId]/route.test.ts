import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { SubscriptionInvoiceResponse } from '@/lib/api/client/types.gen';
import type { NextRequest } from 'next/server';

const getTenantInvoice = vi.hoisted(() => vi.fn());
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
  getTenantInvoice,
}));
vi.mock('@/lib/server/features', () => ({
  FeatureFlagsApiError,
  requireBillingFeature,
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

const context = (tenantId?: string, invoiceId?: string): Parameters<
  (typeof import('./route'))['GET']
>[1] => ({
  params: Promise.resolve({ tenantId, invoiceId }),
});

beforeEach(() => {
  getTenantInvoice.mockReset();
  requireBillingFeature.mockReset();
});

describe('GET /api/v1/billing/tenants/[tenantId]/invoices/[invoiceId]', () => {
  it('returns 403 when billing is disabled', async () => {
    requireBillingFeature.mockRejectedValueOnce(
      new FeatureFlagsApiError(403, 'Billing is disabled.'),
    );
    const { GET } = await loadHandler();

    const response = await GET(
      mockRequest('http://localhost/api/v1/billing/tenants/t1/invoices/in_123'),
      context('t1', 'in_123'),
    );

    expect(response.status).toBe(403);
  });

  it('returns invoice payload', async () => {
    requireBillingFeature.mockResolvedValueOnce(undefined);
    const { GET } = await loadHandler();

    const invoice: SubscriptionInvoiceResponse = {
      invoice_id: 'in_123',
      status: 'paid',
      amount_cents: 1200,
      currency: 'USD',
      period_start: '2025-01-01T00:00:00Z',
      period_end: '2025-02-01T00:00:00Z',
      hosted_invoice_url: 'https://example.com/invoices/in_123',
      created_at: '2025-01-01T00:00:00Z',
    };

    getTenantInvoice.mockResolvedValueOnce(invoice);

    const request = mockRequest(
      'http://localhost/api/v1/billing/tenants/t1/invoices/in_123',
      new Headers({ 'x-tenant-role': 'viewer' }),
    );
    const response = await GET(request, context('t1', 'in_123'));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(invoice);
    expect(getTenantInvoice).toHaveBeenCalledWith('t1', 'in_123', {
      tenantRole: 'viewer',
    });
  });
});
