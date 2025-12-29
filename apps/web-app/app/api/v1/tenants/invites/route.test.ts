import { vi } from 'vitest';
import type { NextRequest } from 'next/server';

import { GET, POST } from './route';

const listTeamInvites = vi.hoisted(() => vi.fn());
const issueTeamInvite = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/team', async () => {
  const actual = await vi.importActual<typeof import('@/lib/server/services/team')>(
    '@/lib/server/services/team',
  );
  return {
    ...actual,
    listTeamInvites,
    issueTeamInvite,
  };
});

const mockRequest = (overrides: Partial<NextRequest> = {}): NextRequest =>
  ({
    json: vi.fn(),
    headers: new Headers(),
    url: 'http://localhost/api/v1/tenants/invites',
    ...overrides,
  }) as unknown as NextRequest;

describe('/api/v1/tenants/invites route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns invite list payload on success', async () => {
    listTeamInvites.mockResolvedValueOnce({
      invites: [
        {
          id: 'invite-1',
          tenantId: 'tenant-1',
          tokenHint: 'abcd',
          invitedEmail: 'new@acme.io',
          role: 'member',
          status: 'active',
          createdByUserId: 'user-1',
          acceptedByUserId: null,
          acceptedAt: null,
          revokedAt: null,
          revokedReason: null,
          expiresAt: null,
          createdAt: '2025-12-02T10:00:00Z',
        },
      ],
      total: 1,
      limit: 50,
      offset: 0,
    });

    const response = await GET(
      mockRequest({
        url: 'http://localhost/api/v1/tenants/invites?status=active',
      }),
    );

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({
      success: true,
      invites: [
        {
          id: 'invite-1',
          tenantId: 'tenant-1',
          tokenHint: 'abcd',
          invitedEmail: 'new@acme.io',
          role: 'member',
          status: 'active',
          createdByUserId: 'user-1',
          acceptedByUserId: null,
          acceptedAt: null,
          revokedAt: null,
          revokedReason: null,
          expiresAt: null,
          createdAt: '2025-12-02T10:00:00Z',
        },
      ],
      total: 1,
      limit: 50,
      offset: 0,
    });
  });

  it('issues a team invite on POST', async () => {
    issueTeamInvite.mockResolvedValueOnce({
      invite: {
        id: 'invite-1',
        tenantId: 'tenant-1',
        tokenHint: 'abcd',
        invitedEmail: 'new@acme.io',
        role: 'member',
        status: 'active',
        createdByUserId: 'user-1',
        acceptedByUserId: null,
        acceptedAt: null,
        revokedAt: null,
        revokedReason: null,
        expiresAt: null,
        createdAt: '2025-12-02T10:00:00Z',
      },
      inviteToken: 'token-123',
    });

    const request = mockRequest({
      json: vi.fn().mockResolvedValue({ invitedEmail: 'new@acme.io', role: 'member' }),
    });

    const response = await POST(request);

    expect(response.status).toBe(201);
    await expect(response.json()).resolves.toEqual({
      success: true,
      data: {
        invite: {
          id: 'invite-1',
          tenantId: 'tenant-1',
          tokenHint: 'abcd',
          invitedEmail: 'new@acme.io',
          role: 'member',
          status: 'active',
          createdByUserId: 'user-1',
          acceptedByUserId: null,
          acceptedAt: null,
          revokedAt: null,
          revokedReason: null,
          expiresAt: null,
          createdAt: '2025-12-02T10:00:00Z',
        },
        inviteToken: 'token-123',
      },
    });
  });
});
