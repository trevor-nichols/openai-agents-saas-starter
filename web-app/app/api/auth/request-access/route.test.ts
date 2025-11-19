import { vi } from 'vitest';
import type { NextRequest } from 'next/server';

import { POST } from './route';

const submitSignupAccessRequest = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/auth/signupGuardrails', () => ({
  submitSignupAccessRequest,
}));

const buildRequest = (payload: unknown): NextRequest =>
  ({
    json: vi.fn().mockResolvedValue(payload),
  }) as unknown as NextRequest;

describe('/api/auth/request-access route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns 202 when the request is accepted', async () => {
    submitSignupAccessRequest.mockResolvedValueOnce({
      policy: 'invite_only',
      invite_required: true,
      request_access_enabled: true,
    });

    const response = await POST(
      buildRequest({
        email: 'secops@example.com',
        organization: 'SecOps',
        fullName: 'Sec Ops',
        acceptTerms: true,
      }),
    );

    expect(response.status).toBe(202);
    await expect(response.json()).resolves.toEqual({
      success: true,
      policy: {
        policy: 'invite_only',
        invite_required: true,
        request_access_enabled: true,
      },
    });
  });

  it('normalizes backend errors', async () => {
    submitSignupAccessRequest.mockRejectedValueOnce(new Error('Rate limit exceeded'));

    const response = await POST(
      buildRequest({
        email: 'bad@example.com',
        organization: 'Bad Actor',
        fullName: 'Bot',
        acceptTerms: true,
      }),
    );

    expect(response.status).toBe(429);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'Rate limit exceeded',
    });
  });
});
