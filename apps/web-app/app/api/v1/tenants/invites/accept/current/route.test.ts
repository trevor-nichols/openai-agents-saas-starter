import { vi } from 'vitest';
import type { NextRequest } from 'next/server';

import { POST } from './route';

const acceptTeamInviteExisting = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/team', async () => {
  const actual = await vi.importActual<typeof import('@/lib/server/services/team')>(
    '@/lib/server/services/team',
  );
  return {
    ...actual,
    acceptTeamInviteExisting,
  };
});

const mockRequest = (overrides: Partial<NextRequest> = {}): NextRequest =>
  ({
    json: vi.fn(),
    headers: new Headers(),
    ...overrides,
  }) as unknown as NextRequest;

describe('/api/v1/tenants/invites/accept/current route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('accepts an invite for current user', async () => {
    acceptTeamInviteExisting.mockResolvedValueOnce({
      id: 'invite-1',
      tenantId: 'tenant-1',
      tokenHint: 'abcd',
      invitedEmail: 'new@acme.io',
      role: 'member',
      status: 'accepted',
      createdByUserId: 'user-1',
      acceptedByUserId: 'user-2',
      acceptedAt: '2025-12-03T10:00:00Z',
      revokedAt: null,
      revokedReason: null,
      expiresAt: null,
      createdAt: '2025-12-02T10:00:00Z',
    });

    const request = mockRequest({
      json: vi.fn().mockResolvedValue({ token: 'token-123' }),
    });

    const response = await POST(request);

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({
      success: true,
      data: {
        id: 'invite-1',
        tenantId: 'tenant-1',
        tokenHint: 'abcd',
        invitedEmail: 'new@acme.io',
        role: 'member',
        status: 'accepted',
        createdByUserId: 'user-1',
        acceptedByUserId: 'user-2',
        acceptedAt: '2025-12-03T10:00:00Z',
        revokedAt: null,
        revokedReason: null,
        expiresAt: null,
        createdAt: '2025-12-02T10:00:00Z',
      },
    });
  });
});
