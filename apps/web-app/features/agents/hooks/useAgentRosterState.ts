import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { useAgentStatuses } from '@/lib/queries/agents';

import type { AgentWorkspaceQueries } from './useAgentWorkspaceData';

type RosterInput = Pick<
  AgentWorkspaceQueries,
  | 'agentsPages'
  | 'agents'
  | 'isLoadingAgents'
  | 'agentsError'
  | 'hasNextAgentsPage'
  | 'fetchNextAgentsPage'
  | 'isFetchingNextAgentsPage'
  | 'toolsError'
>;

interface AgentRosterState {
  agentsWithStatus: AgentWorkspaceQueries['agents'];
  pagedAgentsWithStatus: AgentWorkspaceQueries['agentsPages'];
  visiblePageIndex: number;
  hasPrevPage: boolean;
  rosterLoading: boolean;
  rosterErrorMessage: string | null;
  onNextPage: () => Promise<void>;
  onPrevPage: () => void;
  onPageSelect: (pageIndex: number) => Promise<void>;
}

function applyLastSeen<T extends { name: string; last_seen_at?: string | null }>(
  agents: T[],
  statusMap: Record<string, { last_used?: string | null } | null>,
): T[] {
  return agents.map((agent) => ({
    ...agent,
    last_seen_at: statusMap[agent.name]?.last_used ?? agent.last_seen_at ?? null,
  }));
}

export function useAgentRosterState({
  agentsPages,
  agents,
  isLoadingAgents,
  agentsError,
  hasNextAgentsPage,
  fetchNextAgentsPage,
  isFetchingNextAgentsPage,
  toolsError,
}: RosterInput): AgentRosterState {
  const [pageIndex, setPageIndex] = useState(0);
  const pagesLengthRef = useRef(agentsPages.length);

  useEffect(() => {
    pagesLengthRef.current = agentsPages.length;
  }, [agentsPages.length]);

  const clampedPageIndex = useMemo(() => {
    if (agentsPages.length === 0) {
      return 0;
    }
    return Math.min(pageIndex, agentsPages.length - 1);
  }, [agentsPages.length, pageIndex]);

  const statusQuery = useAgentStatuses(agents.map((agent) => agent.name));

  const agentsWithStatus = useMemo(
    () => applyLastSeen(agents, statusQuery.statusMap),
    [agents, statusQuery.statusMap],
  );

  const pagedAgentsWithStatus = useMemo(
    () =>
      agentsPages.map((page) => ({
        ...page,
        items: applyLastSeen(page.items ?? [], statusQuery.statusMap),
      })),
    [agentsPages, statusQuery.statusMap],
  );

  const pageCount = pagedAgentsWithStatus.length;
  const hasPrevPage = clampedPageIndex > 0;
  const canAdvanceLoadedPage = clampedPageIndex < pageCount - 1;

  const rosterErrorMessage =
    agentsError?.message ?? statusQuery.statusError?.message ?? toolsError ?? null;
  const rosterLoading = isLoadingAgents || statusQuery.isLoadingStatuses;

  const onNextPage = useCallback(async () => {
    if (canAdvanceLoadedPage) {
      setPageIndex((idx) => Math.min(idx + 1, pageCount - 1));
      return;
    }
    if (!hasNextAgentsPage || isFetchingNextAgentsPage) {
      return;
    }
    const result = await fetchNextAgentsPage();
    const nextLength = result.data?.pages?.length ?? pagesLengthRef.current;
    if (nextLength > pageCount) {
      setPageIndex((idx) => Math.min(idx + 1, nextLength - 1));
    }
  }, [
    canAdvanceLoadedPage,
    fetchNextAgentsPage,
    hasNextAgentsPage,
    isFetchingNextAgentsPage,
    pageCount,
  ]);

  const onPrevPage = useCallback(() => {
    if (!hasPrevPage) {
      return;
    }
    setPageIndex((idx) => Math.max(idx - 1, 0));
  }, [hasPrevPage]);

  const onPageSelect = useCallback(
    async (nextIndex: number) => {
      if (nextIndex === clampedPageIndex) {
        return;
      }
      if (nextIndex < clampedPageIndex) {
        setPageIndex(Math.max(0, nextIndex));
        return;
      }

      if (nextIndex < pageCount) {
        setPageIndex(Math.min(nextIndex, pageCount - 1));
        return;
      }

      if (!hasNextAgentsPage || isFetchingNextAgentsPage) {
        return;
      }

      const result = await fetchNextAgentsPage();
      const nextLength = result.data?.pages?.length ?? pagesLengthRef.current;
      if (nextLength > clampedPageIndex) {
        setPageIndex(() => Math.min(nextIndex, nextLength - 1));
      }
    },
    [
      clampedPageIndex,
      fetchNextAgentsPage,
      hasNextAgentsPage,
      isFetchingNextAgentsPage,
      pageCount,
    ],
  );

  return {
    agentsWithStatus,
    pagedAgentsWithStatus,
    visiblePageIndex: clampedPageIndex,
    hasPrevPage,
    rosterLoading,
    rosterErrorMessage,
    onNextPage,
    onPrevPage,
    onPageSelect,
  };
}
