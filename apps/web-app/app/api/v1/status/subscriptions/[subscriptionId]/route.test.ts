import { NextRequest } from 'next/server';
import { vi } from 'vitest';

import { DELETE } from './route';

const unsubscribeStatusSubscriptionViaToken = vi.hoisted(() => vi.fn());
const revokeStatusSubscription = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/statusSubscriptions', () => ({
  unsubscribeStatusSubscriptionViaToken,
  revokeStatusSubscription,
}));

describe('/api/v1/status/subscriptions/[subscriptionId] route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('requires subscriptionId', async () => {
    const response = await DELETE(new NextRequest('https://example.com/api/v1/status/subscriptions/'), {
      params: Promise.resolve({ subscriptionId: '' }),
    } as never);
    expect(response.status).toBe(400);
  });

  it('uses token flow when token provided', async () => {
    const response = await DELETE(
      new NextRequest('https://example.com/api/v1/status/subscriptions/sub-1?token=abc'),
      { params: Promise.resolve({ subscriptionId: 'sub-1' }) } as never,
    );
    expect(unsubscribeStatusSubscriptionViaToken).toHaveBeenCalledWith({ subscriptionId: 'sub-1', token: 'abc' });
    expect(response.status).toBe(200);
  });

  it('calls authenticated revoke when no token', async () => {
    const response = await DELETE(
      new NextRequest('https://example.com/api/v1/status/subscriptions/sub-1'),
      { params: Promise.resolve({ subscriptionId: 'sub-1' }) } as never,
    );
    expect(revokeStatusSubscription).toHaveBeenCalled();
    expect(response.status).toBe(200);
  });
});
