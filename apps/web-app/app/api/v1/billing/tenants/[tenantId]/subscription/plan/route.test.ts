import { vi } from 'vitest';

import type {
  ChangeSubscriptionPlanRequest,
  PlanChangeResponse,
} from '@/lib/api/client/types.gen';
import type { NextRequest } from 'next/server';

import { POST } from './route';

const changeTenantSubscriptionPlan = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/billing', () => ({
  changeTenantSubscriptionPlan,
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

describe('/api/billing/tenants/[tenantId]/subscription/plan route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns plan change payload on success', async () => {
    const requestPayload: ChangeSubscriptionPlanRequest = {
      plan_code: 'pro',
      seat_count: 4,
      timing: 'auto',
    };
    const responsePayload: PlanChangeResponse = {
      subscription: {
        tenant_id: 'tenant-1',
        plan_code: 'starter',
        status: 'active',
        auto_renew: true,
        billing_email: 'admin@example.com',
        starts_at: new Date().toISOString(),
        metadata: {},
      },
      target_plan_code: 'pro',
      timing: 'period_end',
      effective_at: new Date().toISOString(),
      seat_count: 4,
    };

    const request = mockRequest({
      json: vi.fn().mockResolvedValue(requestPayload),
      headers: new Headers({ 'x-tenant-role': 'owner' }),
    });

    changeTenantSubscriptionPlan.mockResolvedValueOnce(responsePayload);

    const response = await POST(request, context('tenant-1'));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(responsePayload);
    expect(changeTenantSubscriptionPlan).toHaveBeenCalledWith('tenant-1', requestPayload, {
      tenantRole: 'owner',
    });
  });

  it('returns 400 when tenant id missing', async () => {
    const request = mockRequest();
    const response = await POST(request, context());

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ message: 'Tenant id is required.' });
    expect(changeTenantSubscriptionPlan).not.toHaveBeenCalled();
  });
});
