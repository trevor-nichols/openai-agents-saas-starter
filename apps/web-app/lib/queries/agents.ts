import { useQuery } from '@tanstack/react-query';

import { fetchAgentStatus, fetchAgents } from '@/lib/api/agents';

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

