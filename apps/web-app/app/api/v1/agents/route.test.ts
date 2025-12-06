import { vi } from 'vitest';

import type { AgentSummary } from '@/lib/api/client/types.gen';

import { GET } from './route';

const listAvailableAgents = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/agents', () => ({
  listAvailableAgents,
}));

describe('/api/agents route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns available agents on success', async () => {
    const agents: AgentSummary[] = [
      {
        name: 'triage',
        status: 'active',
        description: 'Primary orchestrator',
      },
    ];
    listAvailableAgents.mockResolvedValueOnce(agents);

    const response = await GET();

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({
      success: true,
      agents,
    });
    expect(listAvailableAgents).toHaveBeenCalledTimes(1);
  });

  it('returns 500 when service fails', async () => {
    listAvailableAgents.mockRejectedValueOnce(new Error('boom'));

    const response = await GET();

    expect(response.status).toBe(500);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'boom',
    });
  });

  it('returns 401 when missing access token error surfaces', async () => {
    listAvailableAgents.mockRejectedValueOnce(new Error('Missing access token'));

    const response = await GET();

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'Missing access token',
    });
  });
});

