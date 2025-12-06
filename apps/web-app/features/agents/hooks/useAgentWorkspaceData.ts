import { useMemo } from 'react';

import { useAgentStatuses, useAgents } from '@/lib/queries/agents';
import { useConversations } from '@/lib/queries/conversations';
import { useTools } from '@/lib/queries/tools';
import { useContainersQuery } from '@/lib/queries/containers';

import { buildToolsByAgentMap, summarizeToolRegistry } from '../utils/toolTransforms';
import type { ToolRegistrySummary, ToolsByAgentMap } from '../types';
import type { ContainerResponse } from '@/lib/api/client/types.gen';

export interface AgentWorkspaceQueries {
  agents: ReturnType<typeof useAgents>['agents'];
  isLoadingAgents: boolean;
  agentsError: ReturnType<typeof useAgents>['agentsError'];
  containers: ContainerResponse[];
  isLoadingContainers: boolean;
  containersError: Error | null;
  toolsSummary: ToolRegistrySummary;
  toolsByAgent: ToolsByAgentMap;
  tools: ReturnType<typeof useTools>['tools'];
  isLoadingTools: boolean;
  toolsError: ReturnType<typeof useTools>['error'];
  refetchTools: ReturnType<typeof useTools>['refetch'];
  conversationList: ReturnType<typeof useConversations>['conversationList'];
  isLoadingConversations: boolean;
  conversationsError: ReturnType<typeof useConversations>['error'];
  loadConversations: ReturnType<typeof useConversations>['loadConversations'];
  loadMoreConversations: ReturnType<typeof useConversations>['loadMore'];
  hasNextConversationPage: ReturnType<typeof useConversations>['hasNextPage'];
  addConversationToList: ReturnType<typeof useConversations>['addConversationToList'];
  updateConversationInList: ReturnType<typeof useConversations>['updateConversationInList'];
  removeConversationFromList: ReturnType<typeof useConversations>['removeConversationFromList'];
}

export function useAgentWorkspaceData(): AgentWorkspaceQueries {
  const agentsQuery = useAgents();
  const statusQuery = useAgentStatuses(agentsQuery.agents.map((agent) => agent.name));
  const toolsQuery = useTools();
  const conversationsQuery = useConversations();
  const containersQuery = useContainersQuery();

  const agentsWithStatus = useMemo(
    () =>
      agentsQuery.agents.map((agent) => ({
        ...agent,
        last_seen_at: statusQuery.statusMap[agent.name]?.last_used ?? agent.last_seen_at ?? null,
      })),
    [agentsQuery.agents, statusQuery.statusMap],
  );

  const toolsByAgent = useMemo(
    () => buildToolsByAgentMap(agentsWithStatus, toolsQuery.tools),
    [agentsWithStatus, toolsQuery.tools],
  );

  const toolsSummary = useMemo(
    () => summarizeToolRegistry(toolsQuery.tools),
    [toolsQuery.tools],
  );

  return {
    agents: agentsWithStatus,
    isLoadingAgents: agentsQuery.isLoadingAgents || statusQuery.isLoadingStatuses,
    agentsError: agentsQuery.agentsError ?? statusQuery.statusError,
    containers: containersQuery.data?.items ?? [],
    isLoadingContainers: containersQuery.isLoading,
    containersError: (containersQuery.error as Error | null) ?? null,
    toolsSummary,
    toolsByAgent,
    tools: toolsQuery.tools,
    isLoadingTools: toolsQuery.isLoading,
    toolsError: toolsQuery.error,
    refetchTools: toolsQuery.refetch,
    conversationList: conversationsQuery.conversationList,
    isLoadingConversations: conversationsQuery.isLoadingConversations,
    conversationsError: conversationsQuery.error,
    loadConversations: conversationsQuery.loadConversations,
    loadMoreConversations: conversationsQuery.loadMore,
    hasNextConversationPage: conversationsQuery.hasNextPage,
    addConversationToList: conversationsQuery.addConversationToList,
    updateConversationInList: conversationsQuery.updateConversationInList,
    removeConversationFromList: conversationsQuery.removeConversationFromList,
  };
}
