import { useQueries, useQuery } from '@tanstack/react-query';

import { fetchAgentStatus, fetchAgents } from '@/lib/api/agents';
import type { AgentStatus } from '@/types/agents';

import { queryKeys } from './keys';

export function useAgents() {
  const {
    data: agents = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: queryKeys.agents.list(),
    queryFn: fetchAgents,
    staleTime: 30 * 1000,
  });

  return {
    agents,
    isLoadingAgents: isLoading,
    agentsError: error instanceof Error ? error : null,
  };
}

export function useAgentStatuses(agentNames: string[]) {
  const queries = useQueries({
    queries: agentNames.map((agentName) => ({
      queryKey: queryKeys.agents.detail(agentName),
      queryFn: () => fetchAgentStatus(agentName),
      enabled: Boolean(agentName),
      staleTime: 15 * 1000,
    })),
    combine: (results) => results,
  });

  const statusMap = queries.reduce<Record<string, AgentStatus | null>>((acc, query, idx) => {
    const name = agentNames[idx];
    if (!name) {
      return acc;
    }
    acc[name] = (query.data as AgentStatus | null) ?? null;
    return acc;
  }, {});

  const isLoadingStatuses = queries.some((q) => q.isLoading);
  const statusError = (queries.find((q) => q.error)?.error as Error | null) ?? null;

  return {
    statusMap,
    isLoadingStatuses,
    statusError,
  };
}

export function useAgentStatus(agentName: string | null) {
  const shouldFetch = Boolean(agentName);
  const {
    data,
    isLoading,
    error,
  } = useQuery({
    queryKey: agentName ? queryKeys.agents.detail(agentName) : queryKeys.agents.detail(''),
    queryFn: () => fetchAgentStatus(agentName as string),
    enabled: shouldFetch,
    staleTime: 15 * 1000,
  });

  return {
    agentStatus: data ?? null,
    isLoadingAgentStatus: isLoading && shouldFetch,
    agentStatusError: error instanceof Error ? error : null,
  };
}
