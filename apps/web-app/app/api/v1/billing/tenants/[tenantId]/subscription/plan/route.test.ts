import { vi } from 'vitest';

import type { ChangeSubscriptionPlanRequest, PlanChangeResponse } from '@/lib/api/client/types.gen';
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

  it('returns plan change response on success', async () => {
    const requestPayload: ChangeSubscriptionPlanRequest = { plan_code: 'pro', timing: 'period_end', seat_count: 12 };
    const responsePayload: PlanChangeResponse = {
      plan_code: 'pro',
      timing: 'period_end',
      seat_count: 12,
      effective_at: '2026-01-01T00:00:00Z',
      current_period_end: '2025-12-31T00:00:00Z',
      schedule_id: 'sub_sched_123',
    };

    changeTenantSubscriptionPlan.mockResolvedValueOnce(responsePayload);

    const request = mockRequest({ json: vi.fn().mockResolvedValue(requestPayload) });
    const response = await POST(request, context('tenant-1'));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(responsePayload);
    expect(changeTenantSubscriptionPlan).toHaveBeenCalledWith('tenant-1', requestPayload, {
      tenantRole: null,
    });
  });
});
