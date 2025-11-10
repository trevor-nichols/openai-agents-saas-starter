import { vi } from 'vitest';

import type { UsageRecordRequest } from '@/lib/api/client/types.gen';
import type { NextRequest } from 'next/server';

import { POST } from './route';

const recordTenantUsage = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/billing', () => ({
  recordTenantUsage,
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

describe('/api/billing/tenants/[tenantId]/usage route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns 202 on success', async () => {
    const payload: UsageRecordRequest = {
      feature_key: 'messages',
      quantity: 5,
    };

    const request = mockRequest({
      json: vi.fn().mockResolvedValue(payload),
      headers: new Headers({ 'x-tenant-role': 'owner' }),
    });

    recordTenantUsage.mockResolvedValueOnce(undefined);

    const response = await POST(request, context('tenant-1'));

    expect(response.status).toBe(202);
    await expect(response.json()).resolves.toEqual({
      success: true,
      message: 'Usage recorded',
    });
    expect(recordTenantUsage).toHaveBeenCalledWith('tenant-1', payload, {
      tenantRole: 'owner',
    });
  });

  it('returns 400 when tenant id missing', async () => {
    const request = mockRequest();
    const response = await POST(request, context());

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ message: 'Tenant id is required.' });
    expect(recordTenantUsage).not.toHaveBeenCalled();
  });
});

