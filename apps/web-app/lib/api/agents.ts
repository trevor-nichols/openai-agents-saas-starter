import type { AgentListResponse, AgentStatus, AgentSummary } from '@/types/agents';
import { apiV1Path } from '@/lib/apiPaths';
import { collectCursorItems } from './pagination';

export async function fetchAgentsPage(params?: {
  limit?: number;
  cursor?: string | null;
  search?: string | null;
}): Promise<AgentListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set('limit', String(params.limit));
  if (params?.cursor) searchParams.set('cursor', params.cursor);
  if (params?.search) searchParams.set('search', params.search);

  const response = await fetch(
    `${apiV1Path('/agents')}${searchParams.toString() ? `?${searchParams.toString()}` : ''}`,
    { method: 'GET', cache: 'no-store' },
  );

  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as { message?: string };
    throw new Error(payload.message || 'Failed to load agents');
  }

  const result = (await response.json()) as AgentListResponse;
  return {
    items: result.items ?? [],
    next_cursor: result.next_cursor ?? null,
    total: result.total ?? 0,
  };
}

export async function fetchAgents(params?: {
  search?: string | null;
  maxPages?: number;
}): Promise<AgentSummary[]> {
  return collectCursorItems(
    (cursor) =>
      fetchAgentsPage({
        limit: 100,
        cursor,
        search: params?.search ?? null,
      }),
    { maxPages: params?.maxPages },
  );
}

export async function fetchAgentStatus(agentName: string): Promise<AgentStatus> {
  const response = await fetch(apiV1Path(`/agents/${encodeURIComponent(agentName)}/status`), {
    method: 'GET',
    cache: 'no-store',
  });

  if (!response.ok) {
    const errorPayload = (await response.json().catch(() => ({}))) as { message?: string };
    throw new Error(errorPayload.message || 'Failed to load agent status');
  }

  return (await response.json()) as AgentStatus;
}
