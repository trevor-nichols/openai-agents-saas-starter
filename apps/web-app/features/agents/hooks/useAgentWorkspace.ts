'use client';

import { useCallback, useMemo } from 'react';

import { useChatController } from '@/lib/chat';
import {
  useBindAgentContainer,
  useCreateContainer,
  useDeleteContainer,
  useUnbindAgentContainer,
} from '@/lib/queries/containers';

import { useAgentRosterState } from './useAgentRosterState';
import { useAgentWorkspaceData } from './useAgentWorkspaceData';
import { useConversationDetailDrawer } from './useConversationDetailDrawer';

export function useAgentWorkspace() {
  const data = useAgentWorkspaceData();

  const rosterState = useAgentRosterState({
    agentsPages: data.agentsPages,
    agents: data.agents,
    isLoadingAgents: data.isLoadingAgents,
    agentsError: data.agentsError,
    hasNextAgentsPage: data.hasNextAgentsPage,
    fetchNextAgentsPage: data.fetchNextAgentsPage,
    isFetchingNextAgentsPage: data.isFetchingNextAgentsPage,
    toolsError: data.toolsError,
  });

  const chatController = useChatController({
    onConversationAdded: data.addConversationToList,
    onConversationUpdated: data.updateConversationInList,
    onConversationRemoved: data.removeConversationFromList,
    reloadConversations: data.loadConversations,
  });

  const {
    currentConversationId,
    selectedAgent,
    setSelectedAgent,
    sendMessage,
    startNewConversation,
    deleteConversation,
    clearError,
  } = chatController;

  const createContainer = useCreateContainer();
  const deleteContainer = useDeleteContainer();
  const bindContainer = useBindAgentContainer(selectedAgent);
  const unbindContainer = useUnbindAgentContainer(selectedAgent);

  const drawerState = useConversationDetailDrawer({
    chatController,
    loadConversations: data.loadConversations,
  });

  const handleSelectAgent = useCallback(
    (agentName: string) => {
      if (agentName === selectedAgent) {
        return;
      }
      setSelectedAgent(agentName);
      startNewConversation();
    },
    [selectedAgent, setSelectedAgent, startNewConversation],
  );

  const handleRefreshAgents = useCallback(
    () => data.refetchAgents().then(() => undefined),
    [data],
  );

  const rosterProps = useMemo(
    () => ({
      agentsPages: rosterState.pagedAgentsWithStatus,
      visiblePageIndex: rosterState.visiblePageIndex,
      totalAgents: data.agentsTotal,
      hasNextPage: data.hasNextAgentsPage,
      hasPrevPage: rosterState.hasPrevPage,
      onNextPage: rosterState.onNextPage,
      onPrevPage: rosterState.onPrevPage,
      onPageSelect: rosterState.onPageSelect,
      toolsByAgent: data.toolsByAgent,
      summary: data.toolsSummary,
      isLoadingAgents: rosterState.rosterLoading,
      isFetchingNextPage: data.isFetchingNextAgentsPage,
      isLoadingTools: data.isLoadingTools,
      errorMessage: rosterState.rosterErrorMessage,
      onRefreshTools: data.refetchTools,
      onRefreshAgents: handleRefreshAgents,
      selectedAgent,
      onSelectAgent: handleSelectAgent,
    }),
    [
      data.agentsTotal,
      data.hasNextAgentsPage,
      data.isFetchingNextAgentsPage,
      data.isLoadingTools,
      data.refetchTools,
      data.toolsByAgent,
      data.toolsSummary,
      handleRefreshAgents,
      handleSelectAgent,
      rosterState.hasPrevPage,
      rosterState.onNextPage,
      rosterState.onPageSelect,
      rosterState.onPrevPage,
      rosterState.pagedAgentsWithStatus,
      rosterState.rosterErrorMessage,
      rosterState.rosterLoading,
      rosterState.visiblePageIndex,
      selectedAgent,
    ],
  );

  const chatProps = useMemo(
    () => ({
      agents: rosterState.agentsWithStatus,
      agentsError: data.agentsError,
      isLoadingAgents: rosterState.rosterLoading,
      selectedAgent,
      onSelectAgent: handleSelectAgent,
      currentConversationId,
      onClearError: clearError,
      onSendMessage: sendMessage,
      onStartNewConversation: startNewConversation,
      onShowConversationDetail: drawerState.showCurrentConversation,
      chatController,
    }),
    [
      clearError,
      currentConversationId,
      data.agentsError,
      drawerState.showCurrentConversation,
      handleSelectAgent,
      rosterState.agentsWithStatus,
      rosterState.rosterLoading,
      selectedAgent,
      sendMessage,
      startNewConversation,
      chatController,
    ],
  );

  const insightsProps = useMemo(
    () => ({
      conversationList: data.conversationList,
      isLoadingConversations: data.isLoadingConversations,
      conversationsError: data.conversationsError,
      onRefreshConversations: data.loadConversations,
      onLoadMoreConversations: data.loadMoreConversations,
      hasNextConversationPage: data.hasNextConversationPage,
      onSelectConversation: drawerState.openDrawerForConversation,
      toolsSummary: data.toolsSummary,
      toolsByAgent: data.toolsByAgent,
      selectedAgent,
      isLoadingTools: data.isLoadingTools,
      toolsError: data.toolsError,
      onRefreshTools: data.refetchTools,
      containers: data.containers,
      isLoadingContainers: data.isLoadingContainers,
      containersError: data.containersError,
      onCreateContainer: (name: string, memoryLimit?: string | null) =>
        createContainer.mutate({ name, memory_limit: memoryLimit ?? null }),
      onDeleteContainer: (id: string) => deleteContainer.mutate(id),
      onBindContainer: (id: string) => bindContainer.mutate(id),
      onUnbindContainer: () => unbindContainer.mutate(),
    }),
    [
      bindContainer,
      createContainer,
      data,
      deleteContainer,
      drawerState.openDrawerForConversation,
      selectedAgent,
      unbindContainer,
    ],
  );

  const drawerProps = useMemo(
    () => ({
      conversationId: drawerState.detailConversationId,
      open: drawerState.detailDrawerOpen,
      onClose: () => drawerState.setDetailDrawerOpen(false),
      onDeleted: drawerState.handleConversationDeleted,
      onDeleteConversation: deleteConversation,
    }),
    [drawerState, deleteConversation],
  );

  return {
    rosterProps,
    chatProps,
    insightsProps,
    drawerProps,
  };
}
