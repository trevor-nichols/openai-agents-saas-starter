import { vi } from 'vitest';

import type { PaymentMethodResponse } from '@/lib/api/client/types.gen';
import type { NextRequest } from 'next/server';

import { GET } from './route';

const listTenantPaymentMethods = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/billing', () => ({
  listTenantPaymentMethods,
}));

const mockRequest = (overrides: Partial<NextRequest> = {}): NextRequest =>
  ({
    headers: new Headers(),
    ...overrides,
  }) as unknown as NextRequest;

const context = (tenantId?: string): Parameters<typeof GET>[1] => ({
  params: Promise.resolve({ tenantId: tenantId as string }),
});

describe('/api/billing/tenants/[tenantId]/payment-methods route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns payment methods on success', async () => {
    const responsePayload: PaymentMethodResponse[] = [
      { id: 'pm_1', brand: 'visa', last4: '4242', exp_month: 12, exp_year: 2026, is_default: true },
    ];
    listTenantPaymentMethods.mockResolvedValueOnce(responsePayload);

    const request = mockRequest({ headers: new Headers({ 'x-tenant-role': 'owner' }) });
    const response = await GET(request, context('tenant-1'));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(responsePayload);
    expect(listTenantPaymentMethods).toHaveBeenCalledWith('tenant-1', { tenantRole: 'owner' });
  });

  it('returns 400 when tenant id missing', async () => {
    const response = await GET(mockRequest(), context());

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ message: 'Tenant id is required.' });
    expect(listTenantPaymentMethods).not.toHaveBeenCalled();
  });
});
