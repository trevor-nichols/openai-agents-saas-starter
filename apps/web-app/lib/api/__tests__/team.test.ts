import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { fetchTeamMembers, issueTeamInvite, revokeTeamInvite } from '@/lib/api/team';

const originalFetch = global.fetch;

const member = {
  userId: 'user-1',
  tenantId: 'tenant-1',
  email: 'owner@acme.io',
  displayName: 'Owner',
  role: 'owner',
  status: 'active',
  emailVerified: true,
  joinedAt: '2025-12-01T10:00:00Z',
};

const invite = {
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
};

describe('team api', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    if (originalFetch) {
      global.fetch = originalFetch;
    } else {
      // @ts-expect-error cleanup mocked fetch reference
      delete global.fetch;
    }
  });

  it('fetchTeamMembers returns list payload', async () => {
    global.fetch = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          success: true,
          members: [member],
          total: 1,
          limit: 50,
          offset: 0,
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    );

    const result = await fetchTeamMembers();

    expect(result.members).toHaveLength(1);
    expect(result.members[0]?.email).toBe('owner@acme.io');
    expect(result.total).toBe(1);
  });

  it('issueTeamInvite surfaces API errors', async () => {
    global.fetch = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({ success: false, error: 'Invite failed' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } },
      ),
    );

    await expect(
      issueTeamInvite({ invitedEmail: 'new@acme.io', role: 'member' }),
    ).rejects.toThrow('Invite failed');
  });

  it('revokeTeamInvite returns invite summary', async () => {
    global.fetch = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({ success: true, data: invite }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    );

    const result = await revokeTeamInvite('invite-1');

    expect(result.id).toBe('invite-1');
    expect(result.status).toBe('active');
  });
});
