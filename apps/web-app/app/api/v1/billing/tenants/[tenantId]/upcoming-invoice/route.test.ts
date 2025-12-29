import { vi } from 'vitest';

import type { UpcomingInvoicePreviewRequest, UpcomingInvoicePreviewResponse } from '@/lib/api/client/types.gen';
import type { NextRequest } from 'next/server';

import { POST } from './route';

const previewTenantUpcomingInvoice = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/billing', () => ({
  previewTenantUpcomingInvoice,
}));

const mockRequest = (overrides: Partial<NextRequest> = {}): NextRequest =>
  ({
    json: vi.fn(),
    headers: new Headers(),
    ...overrides,
  }) as unknown as NextRequest;

const context = (tenantId?: string): Parameters<typeof POST>[1] => ({
  params: Promise.resolve({ tenantId: tenantId as string }),
});

describe('/api/billing/tenants/[tenantId]/upcoming-invoice route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns preview payload on success', async () => {
    const requestPayload: UpcomingInvoicePreviewRequest = { seat_count: 10 };
    const responsePayload: UpcomingInvoicePreviewResponse = {
      plan_code: 'starter',
      plan_name: 'Starter',
      seat_count: 10,
      amount_due_cents: 4900,
      currency: 'USD',
      period_start: '2025-12-01',
      period_end: '2025-12-31',
      lines: [],
    };

    previewTenantUpcomingInvoice.mockResolvedValueOnce(responsePayload);
    const request = mockRequest({ json: vi.fn().mockResolvedValue(requestPayload) });
    const response = await POST(request, context('tenant-1'));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(responsePayload);
    expect(previewTenantUpcomingInvoice).toHaveBeenCalledWith('tenant-1', requestPayload, {
      tenantRole: null,
    });
  });
});
