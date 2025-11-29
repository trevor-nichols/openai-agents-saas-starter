import { useMemo } from 'react';

import { useAgents } from '@/lib/queries/agents';
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
  const toolsQuery = useTools();
  const conversationsQuery = useConversations();
  const containersQuery = useContainersQuery();

  const toolsByAgent = useMemo(
    () => buildToolsByAgentMap(agentsQuery.agents, toolsQuery.tools),
    [agentsQuery.agents, toolsQuery.tools],
  );

  const toolsSummary = useMemo(
    () => summarizeToolRegistry(toolsQuery.tools),
    [toolsQuery.tools],
  );

  return {
    agents: agentsQuery.agents,
    isLoadingAgents: agentsQuery.isLoadingAgents,
    agentsError: agentsQuery.agentsError,
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
