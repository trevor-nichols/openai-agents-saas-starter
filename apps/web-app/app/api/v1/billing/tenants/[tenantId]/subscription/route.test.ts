import { vi } from 'vitest';

import type {
  StartSubscriptionRequest,
  TenantSubscriptionResponse,
  UpdateSubscriptionRequest,
} from '@/lib/api/client/types.gen';
import type { NextRequest } from 'next/server';

import { GET, PATCH, POST } from './route';

const getTenantSubscription = vi.hoisted(() => vi.fn());
const startTenantSubscription = vi.hoisted(() => vi.fn());
const updateTenantSubscription = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/billing', () => ({
  getTenantSubscription,
  startTenantSubscription,
  updateTenantSubscription,
}));

const mockRequest = (overrides: Partial<NextRequest> = {}): NextRequest =>
  ({
    json: vi.fn(),
    headers: new Headers(),
    ...overrides,
  }) as unknown as NextRequest;

const context = (tenantId?: string): Parameters<typeof GET>[1] => ({
  params: Promise.resolve({ tenantId: tenantId as string }),
});

describe('/api/billing/tenants/[tenantId]/subscription route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('GET', () => {
    it('returns subscription payload on success', async () => {
      const payload: TenantSubscriptionResponse = {
        tenant_id: 'tenant-1',
        plan_code: 'starter',
        status: 'active',
        auto_renew: true,
        billing_email: 'admin@example.com',
        starts_at: new Date().toISOString(),
        metadata: {},
      };
      getTenantSubscription.mockResolvedValueOnce(payload);

      const response = await GET(mockRequest(), context('tenant-1'));

      expect(response.status).toBe(200);
      await expect(response.json()).resolves.toEqual(payload);
      expect(getTenantSubscription).toHaveBeenCalledWith('tenant-1', { tenantRole: null });
    });

    it('returns 400 when tenant id missing', async () => {
      const response = await GET(mockRequest(), context());

      expect(response.status).toBe(400);
      await expect(response.json()).resolves.toEqual({ message: 'Tenant id is required.' });
      expect(getTenantSubscription).not.toHaveBeenCalled();
    });
  });

  describe('POST', () => {
    it('starts a subscription and returns payload', async () => {
      const requestPayload: StartSubscriptionRequest = {
        plan_code: 'starter',
        auto_renew: true,
        billing_email: 'admin@example.com',
      };
      const responsePayload: TenantSubscriptionResponse = {
        tenant_id: 'tenant-1',
        plan_code: 'starter',
        status: 'active',
        auto_renew: true,
        billing_email: 'admin@example.com',
        starts_at: new Date().toISOString(),
        metadata: {},
      };

      const request = mockRequest({
        json: vi.fn().mockResolvedValue(requestPayload),
        headers: new Headers({ 'x-tenant-role': 'owner' }),
      });

      startTenantSubscription.mockResolvedValueOnce(responsePayload);

      const response = await POST(request, context('tenant-1'));

      expect(response.status).toBe(201);
      await expect(response.json()).resolves.toEqual(responsePayload);
      expect(startTenantSubscription).toHaveBeenCalledWith('tenant-1', requestPayload, {
        tenantRole: 'owner',
      });
    });
  });

  describe('PATCH', () => {
    it('updates subscription and returns payload', async () => {
      const requestPayload: UpdateSubscriptionRequest = {
        auto_renew: false,
        billing_email: 'finance@example.com',
      };
      const responsePayload: TenantSubscriptionResponse = {
        tenant_id: 'tenant-1',
        plan_code: 'starter',
        status: 'active',
        auto_renew: false,
        billing_email: 'finance@example.com',
        starts_at: new Date().toISOString(),
        metadata: {},
      };

      const request = mockRequest({
        json: vi.fn().mockResolvedValue(requestPayload),
      });

      updateTenantSubscription.mockResolvedValueOnce(responsePayload);

      const response = await PATCH(request, context('tenant-1'));

      expect(response.status).toBe(200);
      await expect(response.json()).resolves.toEqual(responsePayload);
      expect(updateTenantSubscription).toHaveBeenCalledWith('tenant-1', requestPayload, {
        tenantRole: null,
      });
    });
  });
});
