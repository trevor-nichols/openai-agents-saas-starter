import type { AgentStatus, AgentSummary } from '@/types/agents';

interface AgentsListResponse {
  success: boolean;
  agents?: AgentSummary[];
  error?: string;
}

export async function fetchAgents(): Promise<AgentSummary[]> {
  const response = await fetch('/api/agents', {
    method: 'GET',
    cache: 'no-store',
  });

  const payload = (await response.json()) as AgentsListResponse;

  if (!response.ok || payload.success === false || !payload.agents) {
    throw new Error(payload.error || 'Failed to load agents');
  }

  return payload.agents;
}

export async function fetchAgentStatus(agentName: string): Promise<AgentStatus> {
  const response = await fetch(`/api/agents/${encodeURIComponent(agentName)}/status`, {
    method: 'GET',
    cache: 'no-store',
  });

  if (!response.ok) {
    const errorPayload = (await response.json().catch(() => ({}))) as { message?: string };
    throw new Error(errorPayload.message || 'Failed to load agent status');
  }

  return (await response.json()) as AgentStatus;
}

