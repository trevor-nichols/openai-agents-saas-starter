import { vi } from 'vitest';

import type { NextRequest } from 'next/server';

import { POST } from './route';

const revokeServiceAccountToken = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/auth/serviceAccounts', () => ({
  revokeServiceAccountToken,
}));

const buildRequest = (body?: unknown): NextRequest =>
  ({
    json:
      body !== undefined ? vi.fn().mockResolvedValue(body) : vi.fn().mockRejectedValue(new Error('parse error')),
  }) as unknown as NextRequest;

const context = (jti: string): Parameters<typeof POST>[1] => ({
  params: Promise.resolve({ jti }),
});

describe('/api/auth/service-accounts/tokens/[jti]/revoke route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('revokes a token and returns success payload', async () => {
    const response = await POST(
      buildRequest({ reason: 'suspected leak' }),
      context('token-123'),
    );

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({
      success: true,
      data: { jti: 'token-123' },
    });
    expect(revokeServiceAccountToken).toHaveBeenCalledWith('token-123', 'suspected leak');
  });

  it('handles missing body by passing undefined reason', async () => {
    const response = await POST(buildRequest(undefined), context('token-abc'));

    expect(response.status).toBe(200);
    expect(revokeServiceAccountToken).toHaveBeenCalledWith('token-abc', undefined);
  });

  it('maps auth errors to 401 responses', async () => {
    revokeServiceAccountToken.mockRejectedValueOnce(new Error('Missing access token'));

    const response = await POST(buildRequest({ reason: 'test' }), context('token-xyz'));

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'Missing access token',
    });
  });
});
