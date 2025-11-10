import { vi } from 'vitest';

import { POST } from './route';

const logoutAllSessions = vi.hoisted(() => vi.fn());
const destroySession = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/auth/sessions', () => ({
  logoutAllSessions,
}));

vi.mock('@/lib/auth/session', () => ({
  destroySession,
}));

describe('/api/auth/logout/all route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('logs out all sessions and clears cookies', async () => {
    const response = await POST();

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({ success: true });
    expect(logoutAllSessions).toHaveBeenCalledTimes(1);
    expect(destroySession).toHaveBeenCalledTimes(1);
  });

  it('returns 401 when backend reports missing access token', async () => {
    logoutAllSessions.mockRejectedValueOnce(new Error('Missing access token'));

    const response = await POST();

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'Missing access token',
    });
  });
});

