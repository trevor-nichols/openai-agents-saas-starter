import { useInfiniteQuery, useQueries, useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';

import { fetchAgentStatus, fetchAgents, fetchAgentsPage } from '@/lib/api/agents';
import type { AgentStatus } from '@/types/agents';

import { queryKeys } from './keys';

const DEFAULT_AGENT_PAGE_SIZE = 6;

export function useAgents() {
  const {
    data: agents = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: queryKeys.agents.list(),
    queryFn: () => fetchAgents(),
    staleTime: 30 * 1000,
  });

  return {
    agents,
    isLoadingAgents: isLoading,
    agentsError: error instanceof Error ? error : null,
  };
}

export function useAgentsInfinite(params?: { pageSize?: number; search?: string | null }) {
  const pageSize = params?.pageSize ?? DEFAULT_AGENT_PAGE_SIZE;
  const search = params?.search ?? null;

  const query = useInfiniteQuery({
    queryKey: [...queryKeys.agents.list(), 'paginated', pageSize, search],
    queryFn: ({ pageParam = null }) =>
      fetchAgentsPage({
        limit: pageSize,
        cursor: pageParam,
        search,
      }),
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    initialPageParam: null as string | null,
    staleTime: 30 * 1000,
  });

  const pages = query.data?.pages ?? [];
  const agents = pages.flatMap((page) => page.items ?? []);
  const totalAgents = pages[0]?.total ?? agents.length;

  return {
    pages,
    agents,
    totalAgents,
    isLoadingAgents: query.isLoading,
    agentsError: query.error instanceof Error ? query.error : null,
    hasNextPage: query.hasNextPage ?? false,
    fetchNextPage: query.fetchNextPage,
    isFetchingNextPage: query.isFetchingNextPage,
    refetchAgents: query.refetch,
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

export function useFileSearchAgents() {
  const { agents, isLoadingAgents, agentsError } = useAgents();

  const fileSearchAgents = useMemo(
    () => agents.filter((agent) => agent.tooling?.supports_file_search),
    [agents],
  );

  return {
    agents: fileSearchAgents,
    isLoadingAgents,
    agentsError,
  };
}
