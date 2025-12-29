import { vi } from 'vitest';

import type { SuccessNoDataResponse } from '@/lib/api/client/types.gen';
import type { NextRequest } from 'next/server';

import { DELETE } from './route';

const detachTenantPaymentMethod = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/billing', () => ({
  detachTenantPaymentMethod,
}));

const mockRequest = (overrides: Partial<NextRequest> = {}): NextRequest =>
  ({
    headers: new Headers(),
    ...overrides,
  }) as unknown as NextRequest;

const context = (tenantId?: string, paymentMethodId?: string): Parameters<typeof DELETE>[1] => ({
  params: Promise.resolve({ tenantId: tenantId as string, paymentMethodId: paymentMethodId as string }),
});

describe('/api/billing/tenants/[tenantId]/payment-methods/[paymentMethodId] route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('detaches payment method and returns payload', async () => {
    const responsePayload: SuccessNoDataResponse = { success: true, message: 'Payment method detached.' };
    detachTenantPaymentMethod.mockResolvedValueOnce(responsePayload);

    const request = mockRequest({ headers: new Headers({ 'x-tenant-role': 'owner' }) });
    const response = await DELETE(request, context('tenant-1', 'pm_123'));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(responsePayload);
    expect(detachTenantPaymentMethod).toHaveBeenCalledWith('tenant-1', 'pm_123', {
      tenantRole: 'owner',
    });
  });
});
