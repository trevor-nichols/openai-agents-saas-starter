import { vi } from 'vitest';

import { POST } from './route';

const confirmWebhookChallengeApiV1StatusSubscriptionsChallengePost = vi.hoisted(() => vi.fn());

vi.mock('@/lib/api/client/sdk.gen', () => ({
  confirmWebhookChallengeApiV1StatusSubscriptionsChallengePost,
}));

describe('/api/v1/status/subscriptions/challenge route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns backend response on success', async () => {
    const payload = { success: true, challenge: 'ok' };
    confirmWebhookChallengeApiV1StatusSubscriptionsChallengePost.mockResolvedValueOnce({
      data: payload,
      response: { status: 202 },
    });

    const request = { json: vi.fn().mockResolvedValue({ challenge: 'x' }) } as unknown as Request;

    const response = await POST(request);

    expect(response.status).toBe(202);
    await expect(response.json()).resolves.toEqual(payload);
  });

  it('maps missing token errors', async () => {
    confirmWebhookChallengeApiV1StatusSubscriptionsChallengePost.mockRejectedValueOnce(
      new Error('Missing access token'),
    );
    const request = { json: vi.fn().mockResolvedValue({ challenge: 'x' }) } as unknown as Request;
    const response = await POST(request);
    expect(response.status).toBe(401);
  });
});
