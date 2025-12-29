import { vi } from 'vitest';

import type { PortalSessionRequest, PortalSessionResponse } from '@/lib/api/client/types.gen';
import type { NextRequest } from 'next/server';

import { POST } from './route';

const createTenantPortalSession = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/billing', () => ({
  createTenantPortalSession,
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

describe('/api/billing/tenants/[tenantId]/portal route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns portal session payload on success', async () => {
    const requestPayload: PortalSessionRequest = { billing_email: 'billing@example.com' };
    const responsePayload: PortalSessionResponse = { url: 'https://stripe.example/portal' };

    const request = mockRequest({
      json: vi.fn().mockResolvedValue(requestPayload),
      headers: new Headers({ 'x-tenant-role': 'owner' }),
    });

    createTenantPortalSession.mockResolvedValueOnce(responsePayload);

    const response = await POST(request, context('tenant-1'));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(responsePayload);
    expect(createTenantPortalSession).toHaveBeenCalledWith('tenant-1', requestPayload, {
      tenantRole: 'owner',
    });
  });

  it('returns 400 when tenant id missing', async () => {
    const response = await POST(mockRequest(), context());

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ message: 'Tenant id is required.' });
    expect(createTenantPortalSession).not.toHaveBeenCalled();
  });
});
