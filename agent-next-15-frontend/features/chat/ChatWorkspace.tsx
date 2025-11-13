// File Path: features/chat/ChatWorkspace.tsx
// Description: Client-side orchestrator for the chat workspace.

'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { InlineTag, SectionHeader } from '@/components/ui/foundation';
import { ErrorState } from '@/components/ui/states';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { useChatController } from '@/lib/chat/useChatController';
import { useAgents } from '@/lib/queries/agents';
import { useBillingStream } from '@/lib/queries/billing';
import { useConversations } from '@/lib/queries/conversations';
import { useTools } from '@/lib/queries/tools';
import { toast } from 'sonner';

import { AgentSwitcher } from './components/AgentSwitcher';
import { BillingEventsPanel } from './components/BillingEventsPanel';
import { ChatInterface } from './components/ChatInterface';
import { ConversationDetailDrawer } from '@/components/shared/conversations/ConversationDetailDrawer';
import { ConversationSidebar } from './components/ConversationSidebar';
import { ToolMetadataPanel } from './components/ToolMetadataPanel';

export function ChatWorkspace() {
  const {
    conversationList,
    isLoadingConversations,
    addConversationToList,
    updateConversationInList,
    removeConversationFromList,
    loadConversations,
  } = useConversations();
  const { events: billingEvents, status: billingStreamStatus } = useBillingStream();
  const { agents, isLoadingAgents, agentsError } = useAgents();
  const {
    messages,
    isSending,
    isLoadingHistory,
    isClearingConversation,
    errorMessage,
    currentConversationId,
    selectedAgent,
    setSelectedAgent,
    clearError,
    sendMessage,
    selectConversation,
    startNewConversation,
    deleteConversation,
  } = useChatController({
    onConversationAdded: addConversationToList,
    onConversationUpdated: updateConversationInList,
    onConversationRemoved: removeConversationFromList,
    reloadConversations: loadConversations,
  });
  const { tools, isLoading: isLoadingTools, error: toolsError, refetch: refetchTools } = useTools();
  const [toolDrawerOpen, setToolDrawerOpen] = useState(false);
  const [detailDrawerOpen, setDetailDrawerOpen] = useState(false);

  const handleSelectConversation = useCallback(
    (conversationId: string) => {
      void selectConversation(conversationId);
    },
    [selectConversation],
  );

  const handleNewConversation = useCallback(() => {
    startNewConversation();
  }, [startNewConversation]);

  const handleDeleteConversation = useCallback(
    async (conversationId: string) => {
      if (!conversationId) {
        return;
      }

      const shouldDelete =
        typeof window === 'undefined' ? true : window.confirm('Delete this conversation permanently?');
      if (!shouldDelete) {
        return;
      }

      await deleteConversation(conversationId);
    },
    [deleteConversation],
  );

  const activeAgents = useMemo(() => agents.filter((agent) => agent.status === 'active').length, [agents]);
  const selectedAgentLabel = useMemo(() => selectedAgent.replace(/_/g, ' '), [selectedAgent]);

  const handleExportTranscript = useCallback(() => {
    toast.info('Transcript export is on the roadmap', {
      description: 'We will notify you once CSV/PDF export is available.',
    });
  }, []);

  useEffect(() => {
    if (!errorMessage) {
      return;
    }

    toast.error('Chat workspace error', {
      description: errorMessage,
    });
    clearError();
  }, [clearError, errorMessage]);

  useEffect(() => {
    if (!currentConversationId) {
      setDetailDrawerOpen(false);
    }
  }, [currentConversationId]);

  return (
    <>
      <Sheet open={toolDrawerOpen} onOpenChange={setToolDrawerOpen}>
        <SheetContent side="right" className="w-full overflow-y-auto sm:max-w-md">
          <SheetHeader>
            <SheetTitle>Agent tools</SheetTitle>
            <SheetDescription>Registry context for {selectedAgentLabel}.</SheetDescription>
          </SheetHeader>
          <div className="mt-4">
            <ToolMetadataPanel
              selectedAgent={selectedAgentLabel}
              tools={tools}
              isLoading={isLoadingTools}
              error={toolsError}
              onRefresh={refetchTools}
            />
          </div>
        </SheetContent>
      </Sheet>

      <div className="flex flex-1 flex-col gap-6 xl:flex-row">
        <ConversationSidebar
          conversationList={conversationList}
          isLoadingConversations={isLoadingConversations}
          currentConversationId={currentConversationId}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
          onDeleteConversation={handleDeleteConversation}
          className="xl:w-[320px]"
        />

        <div className="flex w-full flex-1 flex-col gap-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <SectionHeader
              eyebrow="Workspace"
              title="Anything Agent Chat"
              description={
                currentConversationId
                  ? `Conversation ${currentConversationId.substring(0, 12)}…`
                  : 'Start a new conversation to brief your agent.'
              }
              actions={
                <InlineTag tone={agentsError ? 'warning' : activeAgents ? 'positive' : 'default'}>
                  {isLoadingAgents
                    ? 'Loading agents…'
                    : agentsError
                      ? 'Inventory unavailable'
                      : `${activeAgents}/${agents.length || 0} active`}
                </InlineTag>
              }
            />

            <div className="flex w-full flex-col gap-3 lg:max-w-sm">
              <AgentSwitcher
                className="w-full"
                agents={agents}
                selectedAgent={selectedAgent}
                onChange={setSelectedAgent}
                isLoading={isLoadingAgents}
                error={agentsError}
              />
              <div className="flex flex-wrap gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={!currentConversationId}
                  onClick={() => setDetailDrawerOpen(true)}
                >
                  Conversation details
                </Button>
                <Button variant="outline" size="sm" onClick={handleExportTranscript}>
                  Export transcript
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="lg:hidden"
                  onClick={() => setToolDrawerOpen(true)}
                >
                  View tools
                </Button>
              </div>
            </div>
          </div>

          {errorMessage ? <ErrorState message={errorMessage} /> : null}

          <ChatInterface
            messages={messages}
            onSendMessage={sendMessage}
            isSending={isSending}
            currentConversationId={currentConversationId}
            onClearConversation={
              currentConversationId
                ? () => {
                    void handleDeleteConversation(currentConversationId);
                  }
                : undefined
            }
            isClearingConversation={isClearingConversation}
            isLoadingHistory={isLoadingHistory}
            className="min-h-[520px]"
          />

          <BillingEventsPanel events={billingEvents} status={billingStreamStatus} />
        </div>

        <div className="hidden xl:block xl:w-[320px]">
          <ToolMetadataPanel
            selectedAgent={selectedAgentLabel}
            tools={tools}
            isLoading={isLoadingTools}
            error={toolsError}
            onRefresh={refetchTools}
            className="h-full"
          />
        </div>
      </div>

      <ConversationDetailDrawer
        open={detailDrawerOpen}
        onClose={() => setDetailDrawerOpen(false)}
        conversationId={currentConversationId}
        onDeleteConversation={deleteConversation}
      />
    </>
  );
}
