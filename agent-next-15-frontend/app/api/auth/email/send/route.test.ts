import { vi } from 'vitest';

import { POST } from './route';

const sendVerificationEmail = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/auth/email', () => ({
  sendVerificationEmail,
}));

describe('/api/auth/email/send route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns 202 with payload on success', async () => {
    const payload = { success: true, message: 'queued' };
    sendVerificationEmail.mockResolvedValueOnce(payload);

    const response = await POST();

    expect(response.status).toBe(202);
    await expect(response.json()).resolves.toEqual(payload);
  });

  it('returns 401 when backend reports missing token', async () => {
    sendVerificationEmail.mockRejectedValueOnce(new Error('Missing access token'));

    const response = await POST();

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({ message: 'Missing access token' });
  });
});

