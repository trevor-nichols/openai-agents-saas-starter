import { vi } from 'vitest';
import type { NextRequest } from 'next/server';

import { POST } from './route';

const revokeTeamInvite = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/team', async () => {
  const actual = await vi.importActual<typeof import('@/lib/server/services/team')>(
    '@/lib/server/services/team',
  );
  return {
    ...actual,
    revokeTeamInvite,
  };
});

const mockRequest = (overrides: Partial<NextRequest> = {}): NextRequest =>
  ({
    headers: new Headers(),
    ...overrides,
  }) as unknown as NextRequest;

const context = (inviteId?: string): Parameters<typeof POST>[1] => ({
  params: Promise.resolve({ inviteId: inviteId as string }),
});

describe('/api/v1/tenants/invites/[inviteId]/revoke route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('revokes an invite', async () => {
    revokeTeamInvite.mockResolvedValueOnce({
      id: 'invite-1',
      tenantId: 'tenant-1',
      tokenHint: 'abcd',
      invitedEmail: 'new@acme.io',
      role: 'member',
      status: 'revoked',
      createdByUserId: 'user-1',
      acceptedByUserId: null,
      acceptedAt: null,
      revokedAt: '2025-12-03T10:00:00Z',
      revokedReason: 'tenant_admin_action',
      expiresAt: null,
      createdAt: '2025-12-02T10:00:00Z',
    });

    const response = await POST(mockRequest(), context('invite-1'));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({
      success: true,
      data: {
        id: 'invite-1',
        tenantId: 'tenant-1',
        tokenHint: 'abcd',
        invitedEmail: 'new@acme.io',
        role: 'member',
        status: 'revoked',
        createdByUserId: 'user-1',
        acceptedByUserId: null,
        acceptedAt: null,
        revokedAt: '2025-12-03T10:00:00Z',
        revokedReason: 'tenant_admin_action',
        expiresAt: null,
        createdAt: '2025-12-02T10:00:00Z',
      },
    });
  });
});
