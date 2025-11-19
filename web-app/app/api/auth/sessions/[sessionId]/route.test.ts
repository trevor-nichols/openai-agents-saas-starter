import { vi } from 'vitest';

import type { SuccessResponse } from '@/lib/api/client/types.gen';

import { DELETE } from './route';

const revokeUserSession = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/auth/sessions', () => ({
  revokeUserSession,
}));

const context = (sessionId?: string) =>
  ({
    params: {
      sessionId,
    },
  }) as { params: { sessionId?: string } };

describe('/api/auth/sessions/[sessionId] route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns revoked session payload on success', async () => {
    const payload: SuccessResponse = {
      success: true,
      message: 'revoked',
      data: null,
    };
    revokeUserSession.mockResolvedValueOnce(payload);

    const response = await DELETE({} as never, context('session-1'));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(payload);
  });

  it('returns 400 when session id missing', async () => {
    const response = await DELETE({} as never, context());

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ message: 'Session id is required.' });
    expect(revokeUserSession).not.toHaveBeenCalled();
  });

  it('returns 401 when access token missing downstream', async () => {
    revokeUserSession.mockRejectedValueOnce(new Error('Missing access token'));

    const response = await DELETE({} as never, context('session-1'));

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({ message: 'Missing access token' });
  });
});

