import { vi } from 'vitest';

import type { SetupIntentRequest, SetupIntentResponse } from '@/lib/api/client/types.gen';
import type { NextRequest } from 'next/server';

import { POST } from './route';

const createTenantSetupIntent = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/billing', () => ({
  createTenantSetupIntent,
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

describe('/api/billing/tenants/[tenantId]/payment-methods/setup-intent route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('creates a setup intent and returns payload', async () => {
    const requestPayload: SetupIntentRequest = { billing_email: 'billing@example.com' };
    const responsePayload: SetupIntentResponse = { id: 'seti_123', client_secret: 'secret' };
    createTenantSetupIntent.mockResolvedValueOnce(responsePayload);

    const request = mockRequest({
      json: vi.fn().mockResolvedValue(requestPayload),
      headers: new Headers({ 'x-tenant-role': 'owner' }),
    });

    const response = await POST(request, context('tenant-1'));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(responsePayload);
    expect(createTenantSetupIntent).toHaveBeenCalledWith('tenant-1', requestPayload, {
      tenantRole: 'owner',
    });
  });
});
