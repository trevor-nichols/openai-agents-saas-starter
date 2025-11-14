import { vi } from 'vitest';

import type {
  CancelSubscriptionRequest,
  TenantSubscriptionResponse,
} from '@/lib/api/client/types.gen';
import type { NextRequest } from 'next/server';

import { POST } from './route';

const cancelTenantSubscription = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/billing', () => ({
  cancelTenantSubscription,
}));

const mockRequest = (overrides: Partial<NextRequest> = {}): NextRequest =>
  ({
    json: vi.fn(),
    headers: new Headers(),
    ...overrides,
  }) as unknown as NextRequest;

const context = (tenantId?: string) =>
  ({
    params: {
      tenantId,
    },
  }) as { params: { tenantId?: string } };

describe('/api/billing/tenants/[tenantId]/subscription/cancel route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns updated subscription on success', async () => {
    const requestPayload: CancelSubscriptionRequest = {
      cancel_at_period_end: true,
    };
    const responsePayload: TenantSubscriptionResponse = {
      tenant_id: 'tenant-1',
      plan_code: 'starter',
      status: 'canceled',
      auto_renew: false,
      billing_email: 'admin@example.com',
      starts_at: new Date().toISOString(),
      metadata: {},
    };

    const request = mockRequest({
      json: vi.fn().mockResolvedValue(requestPayload),
      headers: new Headers({ 'x-tenant-role': 'owner' }),
    });

    cancelTenantSubscription.mockResolvedValueOnce(responsePayload);

    const response = await POST(request, context('tenant-1'));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(responsePayload);
    expect(cancelTenantSubscription).toHaveBeenCalledWith('tenant-1', requestPayload, {
      tenantRole: 'owner',
    });
  });

  it('returns 400 when tenant id missing', async () => {
    const request = mockRequest();
    const response = await POST(request, context());

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ message: 'Tenant id is required.' });
    expect(cancelTenantSubscription).not.toHaveBeenCalled();
  });
});

