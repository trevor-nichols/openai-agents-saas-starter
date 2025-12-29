import { vi } from 'vitest';
import type { NextRequest } from 'next/server';

import { GET, POST } from './route';

const listTeamMembers = vi.hoisted(() => vi.fn());
const addTeamMember = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/team', async () => {
  const actual = await vi.importActual<typeof import('@/lib/server/services/team')>(
    '@/lib/server/services/team',
  );
  return {
    ...actual,
    listTeamMembers,
    addTeamMember,
  };
});

const mockRequest = (overrides: Partial<NextRequest> = {}): NextRequest =>
  ({
    json: vi.fn(),
    headers: new Headers(),
    url: 'http://localhost/api/v1/tenants/members',
    ...overrides,
  }) as unknown as NextRequest;

describe('/api/v1/tenants/members route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns member list payload on success', async () => {
    listTeamMembers.mockResolvedValueOnce({
      members: [
        {
          userId: 'user-1',
          tenantId: 'tenant-1',
          email: 'owner@acme.io',
          displayName: 'Owner',
          role: 'owner',
          status: 'active',
          emailVerified: true,
          joinedAt: '2025-12-01T10:00:00Z',
        },
      ],
      total: 1,
      limit: 50,
      offset: 0,
    });

    const response = await GET(
      mockRequest({
        url: 'http://localhost/api/v1/tenants/members?limit=50&offset=0',
      }),
    );

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({
      success: true,
      members: [
        {
          userId: 'user-1',
          tenantId: 'tenant-1',
          email: 'owner@acme.io',
          displayName: 'Owner',
          role: 'owner',
          status: 'active',
          emailVerified: true,
          joinedAt: '2025-12-01T10:00:00Z',
        },
      ],
      total: 1,
      limit: 50,
      offset: 0,
    });
  });

  it('creates a member on POST', async () => {
    addTeamMember.mockResolvedValueOnce({
      userId: 'user-2',
      tenantId: 'tenant-1',
      email: 'member@acme.io',
      displayName: 'Member',
      role: 'member',
      status: 'active',
      emailVerified: true,
      joinedAt: '2025-12-02T10:00:00Z',
    });

    const request = mockRequest({
      json: vi.fn().mockResolvedValue({ email: 'member@acme.io', role: 'member' }),
    });

    const response = await POST(request);

    expect(response.status).toBe(201);
    await expect(response.json()).resolves.toEqual({
      success: true,
      data: {
        userId: 'user-2',
        tenantId: 'tenant-1',
        email: 'member@acme.io',
        displayName: 'Member',
        role: 'member',
        status: 'active',
        emailVerified: true,
        joinedAt: '2025-12-02T10:00:00Z',
      },
    });
  });
});
