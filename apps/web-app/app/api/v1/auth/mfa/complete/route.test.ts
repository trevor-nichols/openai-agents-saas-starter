import { vi } from 'vitest';

import { POST } from './route';

const completeMfaChallengeApiV1AuthMfaCompletePost = vi.hoisted(() => vi.fn());
const createApiClient = vi.hoisted(() => vi.fn());
const persistSessionCookies = vi.hoisted(() => vi.fn());

vi.mock('@/lib/api/client/sdk.gen', () => ({
  completeMfaChallengeApiV1AuthMfaCompletePost,
}));

vi.mock('@/lib/server/apiClient', () => ({
  createApiClient,
}));

vi.mock('@/lib/auth/cookies', () => ({
  persistSessionCookies,
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

    const client = Symbol('client');
    createApiClient.mockReturnValue(client);
    persistSessionCookies.mockResolvedValue(undefined as unknown as void);
    completeMfaChallengeApiV1AuthMfaCompletePost.mockResolvedValue({ data: { access_token: 'a', refresh_token: 'r', expires_at: 'x', refresh_expires_at: 'y', kid: 'k', refresh_kid: 'rk', scopes: [], tenant_id: 't', user_id: 'u' } });

    const request = {
      json: vi.fn().mockResolvedValue(payload),
    } as unknown as Request;

    const response = await POST(request);

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({ success: true });
    expect(completeMfaChallengeApiV1AuthMfaCompletePost).toHaveBeenCalledWith({
      client,
      throwOnError: true,
      body: payload,
    });
  });
});
