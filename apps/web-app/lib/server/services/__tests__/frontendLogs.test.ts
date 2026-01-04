import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { createHmac } from 'node:crypto';

import { forwardFrontendLog } from '../frontendLogs';

const createApiClient = vi.hoisted(() => vi.fn());
const ingestFrontendLogApiV1LogsPost = vi.hoisted(() => vi.fn());
const jsonBodySerializer = vi.hoisted(() => ({
  bodySerializer: vi.fn(),
}));

vi.mock('../../apiClient', () => ({
  createApiClient,
}));

vi.mock('@/lib/api/client/sdk.gen', () => ({
  ingestFrontendLogApiV1LogsPost,
}));

vi.mock('@/lib/api/client/core/bodySerializer.gen', () => ({
  jsonBodySerializer,
}));


describe('forwardFrontendLog', () => {
  const originalSecret = process.env.FRONTEND_LOG_SHARED_SECRET;

  beforeEach(() => {
    vi.clearAllMocks();
    process.env.FRONTEND_LOG_SHARED_SECRET = 'secret';
  });

  afterEach(() => {
    vi.restoreAllMocks();
    if (originalSecret === undefined) {
      delete process.env.FRONTEND_LOG_SHARED_SECRET;
    } else {
      process.env.FRONTEND_LOG_SHARED_SECRET = originalSecret;
    }
  });

  it('signs the serialized payload and sends the same bytes', async () => {
    const payload = { event: 'ui.click', fields: { size: '1' } } as never;
    jsonBodySerializer.bodySerializer.mockReturnValue('serialized-body');
    createApiClient.mockReturnValue('client');
    ingestFrontendLogApiV1LogsPost.mockResolvedValue({
      data: '',
      response: new Response('', { status: 202 }),
    });

    await forwardFrontendLog({ payload });

    expect(jsonBodySerializer.bodySerializer).toHaveBeenCalledWith(payload);
    const expectedSignature = createHmac('sha256', 'secret')
      .update('serialized-body')
      .digest('hex');

    const call = ingestFrontendLogApiV1LogsPost.mock.calls[0]?.[0];
    expect(call.body).toBe(payload);
    expect(call.headers).toMatchObject({ 'X-Log-Signature': expectedSignature });
    expect(call.bodySerializer?.(payload)).toBe('serialized-body');
  });
});
