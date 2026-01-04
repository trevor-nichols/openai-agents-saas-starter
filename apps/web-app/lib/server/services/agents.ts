import 'server-only';

import {
  getAgentStatusApiV1AgentsAgentNameStatusGet,
  listAvailableAgentsApiV1AgentsGet,
} from '@/lib/api/client/sdk.gen';
import type { AgentListResponse, AgentStatus, AgentSummary } from '@/lib/api/client/types.gen';

import { getServerApiClient } from '../apiClient';

/**
 * Fetch a paginated slice of agents currently registered with the platform.
 */
export async function listAvailableAgentsPage(params?: {
  limit?: number;
  cursor?: string | null;
  search?: string | null;
}): Promise<AgentListResponse> {
  const { client, auth } = await getServerApiClient();

  const response = await listAvailableAgentsApiV1AgentsGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    query: {
      limit: params?.limit,
      cursor: params?.cursor ?? undefined,
      search: params?.search ?? undefined,
    },
  });

  return response.data ?? { items: [], next_cursor: null, total: 0 };
}

/**
 * Fetch all agents currently registered with the platform (first page only).
 */
export async function listAvailableAgents(): Promise<AgentSummary[]> {
  const page = await listAvailableAgentsPage();
  return page.items ?? [];
}

/**
 * Fetch detailed status information for a specific agent.
 */
export async function getAgentStatus(agentName: string): Promise<AgentStatus> {
  if (!agentName) {
    throw new Error('Agent name is required.');
  }

  const { client, auth } = await getServerApiClient();

  const response = await getAgentStatusApiV1AgentsAgentNameStatusGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    path: {
      agent_name: agentName,
    },
  });

  const payload = response.data;
  if (!payload) {
    throw new Error('Agent not found.');
  }

  return payload;
}
