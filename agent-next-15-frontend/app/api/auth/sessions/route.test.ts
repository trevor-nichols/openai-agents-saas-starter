import { vi } from 'vitest';

import type { NextRequest } from 'next/server';
import type { UserSessionListResponse } from '@/lib/api/client/types.gen';

import { GET } from './route';

const listUserSessions = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/auth/sessions', () => ({
  listUserSessions,
}));

const buildRequest = (url: string): NextRequest =>
  ({
    url,
  }) as unknown as NextRequest;

describe('/api/auth/sessions route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns sessions payload with success flag', async () => {
    const payload: UserSessionListResponse = {
      sessions: [],
      total: 0,
      limit: 20,
      offset: 0,
    };
    listUserSessions.mockResolvedValueOnce(payload);

    const response = await GET(buildRequest('https://example.com/api/auth/sessions'));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({
      success: true,
      ...payload,
    });
    expect(listUserSessions).toHaveBeenCalledWith({
      includeRevoked: undefined,
      limit: undefined,
      offset: undefined,
      tenantId: null,
    });
  });

  it('passes query params through to service', async () => {
    const payload: UserSessionListResponse = {
      sessions: [],
      total: 0,
      limit: 5,
      offset: 5,
    };
    listUserSessions.mockResolvedValueOnce(payload);

    const response = await GET(
      buildRequest(
        'https://example.com/api/auth/sessions?include_revoked=true&limit=5&offset=5&tenant_id=abc',
      ),
    );

    expect(response.status).toBe(200);
    expect(listUserSessions).toHaveBeenCalledWith({
      includeRevoked: true,
      limit: 5,
      offset: 5,
      tenantId: 'abc',
    });
  });

  it('returns 401 when missing access token message bubbles up', async () => {
    listUserSessions.mockRejectedValueOnce(new Error('Missing access token'));

    const response = await GET(buildRequest('https://example.com/api/auth/sessions'));

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'Missing access token',
    });
  });
});

