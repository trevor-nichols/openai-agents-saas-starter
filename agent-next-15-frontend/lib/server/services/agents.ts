'use server';

import {
  getAgentStatusApiV1AgentsAgentNameStatusGet,
  listAvailableAgentsApiV1AgentsGet,
} from '@/lib/api/client/sdk.gen';
import type { AgentStatus, AgentSummary } from '@/lib/api/client/types.gen';

import { getServerApiClient } from '../apiClient';

/**
 * Fetch all agents currently registered with the platform.
 */
export async function listAvailableAgents(): Promise<AgentSummary[]> {
  const { client, auth } = await getServerApiClient();

  const response = await listAvailableAgentsApiV1AgentsGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
  });

  return response.data ?? [];
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

