import { vi } from 'vitest';
import type { NextRequest } from 'next/server';

import { DELETE } from './route';

const removeTeamMember = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/team', async () => {
  const actual = await vi.importActual<typeof import('@/lib/server/services/team')>(
    '@/lib/server/services/team',
  );
  return {
    ...actual,
    removeTeamMember,
  };
});

const mockRequest = (overrides: Partial<NextRequest> = {}): NextRequest =>
  ({
    headers: new Headers(),
    ...overrides,
  }) as unknown as NextRequest;

const context = (userId?: string): Parameters<typeof DELETE>[1] => ({
  params: Promise.resolve({ userId: userId as string }),
});

describe('/api/v1/tenants/members/[userId] route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('removes a member', async () => {
    removeTeamMember.mockResolvedValueOnce({ message: 'Member removed successfully.' });

    const response = await DELETE(mockRequest(), context('user-1'));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({
      success: true,
      message: 'Member removed successfully.',
    });
  });
});
