import { vi } from 'vitest';

import type { NextRequest } from 'next/server';

import { POST } from './route';

const issueServiceAccountToken = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/auth/serviceAccounts', () => ({
  issueServiceAccountToken,
}));

const buildRequest = (body: unknown): NextRequest =>
  ({
    json: vi.fn().mockResolvedValue(body),
  }) as unknown as NextRequest;

describe('/api/auth/service-accounts/browser-issue route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns issuance payload on success', async () => {
    issueServiceAccountToken.mockResolvedValueOnce({
      refreshToken: 'rt',
      account: 'ci',
      tenantId: 'tenant-1',
      scopes: ['conversations:read'],
      expiresAt: '2025-01-01T00:00:00Z',
      issuedAt: '2025-01-01T00:00:00Z',
      kid: 'kid-1',
      tokenUse: 'refresh',
    });

    const response = await POST(
      buildRequest({
        account: 'ci',
        scopes: ['conversations:read'],
        tenant_id: 'tenant-1',
        reason: 'Rotate credentials',
      }),
    );

    expect(response.status).toBe(201);
    await expect(response.json()).resolves.toEqual({
      success: true,
      data: expect.objectContaining({ account: 'ci' }),
    });
  });

  it('maps errors to JSON payloads', async () => {
    issueServiceAccountToken.mockRejectedValueOnce(new Error('rate limit'));

    const response = await POST(
      buildRequest({
        account: 'ci',
        scopes: ['conversations:read'],
        tenant_id: 'tenant-1',
        reason: 'Rotate credentials',
      }),
    );

    expect(response.status).toBe(429);
    await expect(response.json()).resolves.toEqual({ success: false, error: 'rate limit' });
  });
});
