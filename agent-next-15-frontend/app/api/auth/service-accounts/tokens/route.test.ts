import { vi } from 'vitest';

import type { NextRequest } from 'next/server';
import type { ServiceAccountTokenListResult } from '@/types/serviceAccounts';

import { GET } from './route';

const listServiceAccountTokens = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/auth/serviceAccounts', () => ({
  listServiceAccountTokens,
}));

const buildRequest = (url: string): NextRequest =>
  ({
    url,
  }) as unknown as NextRequest;

describe('/api/auth/service-accounts/tokens route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns service-account tokens with success flag', async () => {
    const payload: ServiceAccountTokenListResult = {
      tokens: [],
      total: 0,
      limit: 25,
      offset: 0,
    };
    listServiceAccountTokens.mockResolvedValueOnce(payload);

    const response = await GET(
      buildRequest(
        'https://example.com/api/auth/service-accounts/tokens?account=ci&status=revoked&limit=25&offset=0',
      ),
    );

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({
      success: true,
      tokens: payload.tokens,
      total: payload.total,
      limit: payload.limit,
      offset: payload.offset,
    });
    expect(listServiceAccountTokens).toHaveBeenCalledWith({
      account: 'ci',
      fingerprint: undefined,
      status: 'revoked',
      tenantId: undefined,
      includeGlobal: undefined,
      limit: 25,
      offset: 0,
    });
  });

  it('passes optional filters through to the service', async () => {
    const payload: ServiceAccountTokenListResult = {
      tokens: [],
      total: 0,
      limit: 10,
      offset: 5,
    };
    listServiceAccountTokens.mockResolvedValueOnce(payload);

    const response = await GET(
      buildRequest(
        'https://example.com/api/auth/service-accounts/tokens?fingerprint=runner-1&tenant_id=tenant-123&include_global=true',
      ),
    );

    expect(response.status).toBe(200);
    expect(listServiceAccountTokens).toHaveBeenCalledWith({
      account: undefined,
      fingerprint: 'runner-1',
      status: undefined,
      tenantId: 'tenant-123',
      includeGlobal: true,
      limit: undefined,
      offset: undefined,
    });
  });

  it('returns 401 when auth is missing', async () => {
    listServiceAccountTokens.mockRejectedValueOnce(new Error('Missing access token'));

    const response = await GET(buildRequest('https://example.com/api/auth/service-accounts/tokens'));

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'Missing access token',
    });
  });
});
