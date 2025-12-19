import { vi } from 'vitest';

import type { AgentSummary } from '@/lib/api/client/types.gen';

import { GET } from './route';

const listAvailableAgentsPage = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/agents', () => ({
  listAvailableAgentsPage,
}));

describe('/api/agents route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns available agents on success', async () => {
    const payload = {
      items: [
        {
          name: 'triage',
          status: 'active',
          description: 'Primary orchestrator',
        } satisfies AgentSummary,
      ],
      next_cursor: 'next',
      total: 2,
    };
    listAvailableAgentsPage.mockResolvedValueOnce(payload);

    const response = await GET(
      new Request('http://localhost/api/v1/agents?limit=1&cursor=triage&search=tri'),
    );

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(payload);
    expect(listAvailableAgentsPage).toHaveBeenCalledWith({
      limit: 1,
      cursor: 'triage',
      search: 'tri',
    });
  });

  it('returns 500 when service fails', async () => {
    listAvailableAgentsPage.mockRejectedValueOnce(new Error('boom'));

    const response = await GET(new Request('http://localhost/api/v1/agents'));

    expect(response.status).toBe(500);
    await expect(response.json()).resolves.toEqual({ message: 'boom' });
  });

  it('returns 401 when missing access token error surfaces', async () => {
    listAvailableAgentsPage.mockRejectedValueOnce(new Error('Missing access token'));

    const response = await GET(new Request('http://localhost/api/v1/agents'));

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({ message: 'Missing access token' });
  });
});
