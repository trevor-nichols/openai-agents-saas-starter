import { vi } from 'vitest';

import { POST } from './route';

const completeMfaChallenge = vi.hoisted(() => vi.fn());
const persistSessionFromResponse = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/auth/mfa', () => ({
  completeMfaChallenge,
}));

vi.mock('@/lib/auth/session', () => ({
  persistSessionFromResponse,
}));

describe('/api/v1/auth/mfa/complete', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('posts challenge payload and returns tokens', async () => {
    const payload = {
      challenge_token: 'ct',
      method_id: 'm1',
      code: '123456',
    };

    persistSessionFromResponse.mockResolvedValue(undefined as unknown as void);
    completeMfaChallenge.mockResolvedValue({ access_token: 'a', refresh_token: 'r', expires_at: 'x', refresh_expires_at: 'y', kid: 'k', refresh_kid: 'rk', scopes: [], tenant_id: 't', user_id: 'u' });

    const request = {
      json: vi.fn().mockResolvedValue(payload),
    } as unknown as Request;

    const response = await POST(request);

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({ success: true });
    expect(completeMfaChallenge).toHaveBeenCalledWith(payload);
  });
});
