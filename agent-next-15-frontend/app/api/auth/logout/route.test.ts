import { vi } from 'vitest';

import { POST } from './route';

const logoutSession = vi.hoisted(() => vi.fn());
const destroySession = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/auth/sessions', () => ({
  logoutSession,
}));

vi.mock('@/lib/auth/session', () => ({
  destroySession,
}));

describe('/api/auth/logout route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('logs out and clears session cookies', async () => {
    const request = {
      json: vi.fn().mockResolvedValue({ refresh_token: 'token' }),
    } as never;

    const response = await POST(request);

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({ success: true });
    expect(logoutSession).toHaveBeenCalledWith({ refresh_token: 'token' });
    expect(destroySession).toHaveBeenCalledTimes(1);
  });

  it('returns 401 when service reports missing token', async () => {
    const request = {
      json: vi.fn().mockResolvedValue({ refresh_token: 'token' }),
    } as never;
    logoutSession.mockRejectedValueOnce(new Error('Missing access token'));

    const response = await POST(request);

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'Missing access token',
    });
  });
});

