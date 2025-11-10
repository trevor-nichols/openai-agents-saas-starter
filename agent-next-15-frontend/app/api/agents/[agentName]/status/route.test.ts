import { vi } from 'vitest';

import type { AgentStatus } from '@/lib/api/client/types.gen';
import type { NextRequest } from 'next/server';

import { GET } from './route';

const getAgentStatus = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/agents', () => ({
  getAgentStatus,
}));

const context = (agentName?: string) =>
  ({ params: { agentName } } as { params: { agentName?: string } });

describe('/api/agents/[agentName]/status route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns agent status on success', async () => {
    const statusPayload: AgentStatus = {
      name: 'triage',
      status: 'active',
      last_used: new Date().toISOString(),
      total_conversations: 10,
    };
    getAgentStatus.mockResolvedValueOnce(statusPayload);

    const response = await GET({} as NextRequest, context('triage'));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(statusPayload);
    expect(getAgentStatus).toHaveBeenCalledWith('triage');
  });

  it('returns 400 when agent name missing', async () => {
    const response = await GET({} as NextRequest, context());

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ message: 'Agent name is required.' });
    expect(getAgentStatus).not.toHaveBeenCalled();
  });

  it('maps not found errors to 404', async () => {
    getAgentStatus.mockRejectedValueOnce(new Error('Agent not found'));

    const response = await GET({} as NextRequest, context('missing-agent'));

    expect(response.status).toBe(404);
    await expect(response.json()).resolves.toEqual({ message: 'Agent not found' });
  });
});

