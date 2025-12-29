import { vi } from 'vitest';
import type { NextRequest } from 'next/server';

import { PATCH } from './route';

const updateTeamMemberRole = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/team', async () => {
  const actual = await vi.importActual<typeof import('@/lib/server/services/team')>(
    '@/lib/server/services/team',
  );
  return {
    ...actual,
    updateTeamMemberRole,
  };
});

const mockRequest = (overrides: Partial<NextRequest> = {}): NextRequest =>
  ({
    json: vi.fn(),
    headers: new Headers(),
    ...overrides,
  }) as unknown as NextRequest;

const context = (userId?: string): Parameters<typeof PATCH>[1] => ({
  params: Promise.resolve({ userId: userId as string }),
});

describe('/api/v1/tenants/members/[userId]/role route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('updates a member role', async () => {
    updateTeamMemberRole.mockResolvedValueOnce({
      userId: 'user-1',
      tenantId: 'tenant-1',
      email: 'owner@acme.io',
      displayName: 'Owner',
      role: 'admin',
      status: 'active',
      emailVerified: true,
      joinedAt: '2025-12-01T10:00:00Z',
    });

    const request = mockRequest({
      json: vi.fn().mockResolvedValue({ role: 'admin' }),
    });

    const response = await PATCH(request, context('user-1'));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({
      success: true,
      data: {
        userId: 'user-1',
        tenantId: 'tenant-1',
        email: 'owner@acme.io',
        displayName: 'Owner',
        role: 'admin',
        status: 'active',
        emailVerified: true,
        joinedAt: '2025-12-01T10:00:00Z',
      },
    });
  });
});
