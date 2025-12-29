import { vi } from 'vitest';

import type { SuccessNoDataResponse } from '@/lib/api/client/types.gen';
import type { NextRequest } from 'next/server';

import { POST } from './route';

const setTenantDefaultPaymentMethod = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/billing', () => ({
  setTenantDefaultPaymentMethod,
}));

const mockRequest = (overrides: Partial<NextRequest> = {}): NextRequest =>
  ({
    headers: new Headers(),
    ...overrides,
  }) as unknown as NextRequest;

const context = (tenantId?: string, paymentMethodId?: string): Parameters<typeof POST>[1] => ({
  params: Promise.resolve({ tenantId: tenantId as string, paymentMethodId: paymentMethodId as string }),
});

describe('/api/billing/tenants/[tenantId]/payment-methods/[paymentMethodId]/default route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('sets default payment method and returns payload', async () => {
    const responsePayload: SuccessNoDataResponse = { success: true, message: 'Default updated.' };
    setTenantDefaultPaymentMethod.mockResolvedValueOnce(responsePayload);

    const request = mockRequest({ headers: new Headers({ 'x-tenant-role': 'owner' }) });
    const response = await POST(request, context('tenant-1', 'pm_123'));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(responsePayload);
    expect(setTenantDefaultPaymentMethod).toHaveBeenCalledWith('tenant-1', 'pm_123', {
      tenantRole: 'owner',
    });
  });

  it('returns 400 when payment method id missing', async () => {
    const response = await POST(mockRequest(), context('tenant-1'));

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ message: 'Payment method id is required.' });
    expect(setTenantDefaultPaymentMethod).not.toHaveBeenCalled();
  });
});
