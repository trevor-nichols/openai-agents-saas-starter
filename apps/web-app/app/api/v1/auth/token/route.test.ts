import { vi } from 'vitest';

import type { UserSessionTokens } from '@/lib/types/auth';

import { POST } from './route';

const exchangeCredentials = vi.hoisted(() => vi.fn());

vi.mock('@/lib/auth/session', () => ({
  exchangeCredentials,
}));

describe('/api/v1/auth/token route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns 400 when email or password missing', async () => {
    const request = {
      json: vi.fn().mockResolvedValue({ email: 'a@example.com' }),
    } as unknown as Request;

    const response = await POST(request);

    expect(response.status).toBe(400);
  });

  it('returns tokens on success', async () => {
    const tokens: UserSessionTokens = {
      access_token: 'a',
      refresh_token: 'r',
      token_type: 'bearer',
      expires_at: '2025-12-31T00:00:00Z',
      refresh_expires_at: '2026-01-07T00:00:00Z',
      kid: 'kid',
      refresh_kid: 'rkid',
      scopes: ['chat'],
      tenant_id: 't',
      user_id: 'u',
    };
    exchangeCredentials.mockResolvedValueOnce(tokens);

    const request = {
      json: vi.fn().mockResolvedValue({ email: 'a@example.com', password: 'pw', tenant_id: null }),
    } as unknown as Request;

    const response = await POST(request);

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(tokens);
    expect(exchangeCredentials).toHaveBeenCalledWith({
      email: 'a@example.com',
      password: 'pw',
      tenant_id: null,
    });
  });

  it('maps invalid errors to 401', async () => {
    exchangeCredentials.mockRejectedValueOnce(new Error('Invalid credentials'));
    const request = {
      json: vi.fn().mockResolvedValue({ email: 'a@example.com', password: 'pw' }),
    } as unknown as Request;

    const response = await POST(request);

    expect(response.status).toBe(401);
  });
});
