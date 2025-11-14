// File Path: features/chat/ChatWorkspace.tsx
// Description: Client-side orchestrator for the chat workspace.

'use client';

import { useEffect } from 'react';

import { Button } from '@/components/ui/button';
import { InlineTag, SectionHeader } from '@/components/ui/foundation';
import { ErrorState } from '@/components/ui/states';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/components/ui/sheet';

import { ConversationDetailDrawer } from '@/components/shared/conversations/ConversationDetailDrawer';

import { AgentSwitcher } from './components/AgentSwitcher';
import { BillingEventsPanel } from './components/BillingEventsPanel';
import { ChatInterface } from './components/ChatInterface';
import { ConversationSidebar } from './components/ConversationSidebar';
import { ToolMetadataPanel } from './components/ToolMetadataPanel';
import { CHAT_COPY } from './constants';
import { useChatWorkspace } from './hooks/useChatWorkspace';
import { formatConversationLabel } from './utils/formatters';

export function ChatWorkspace() {
  const {
    conversationList,
    isLoadingConversations,
    billingEvents,
    billingStreamStatus,
    agents,
    isLoadingAgents,
    agentsError,
    messages,
    isSending,
    isLoadingHistory,
    isClearingConversation,
    errorMessage,
    currentConversationId,
    selectedAgent,
    selectedAgentLabel,
    toolDrawerOpen,
    setToolDrawerOpen,
    detailDrawerOpen,
    setDetailDrawerOpen,
    isLoadingTools,
    tools,
    toolsError,
    refetchTools,
    activeAgents,
    handleSelectConversation,
    handleNewConversation,
    handleDeleteConversation,
    handleExportTranscript,
    handleWorkspaceError,
    sendMessage,
    setSelectedAgent,
  } = useChatWorkspace();

  useEffect(() => {
    handleWorkspaceError();
  }, [handleWorkspaceError]);

  useEffect(() => {
    if (!currentConversationId) {
      setDetailDrawerOpen(false);
    }
  }, [currentConversationId, setDetailDrawerOpen]);

  return (
    <>
      <Sheet open={toolDrawerOpen} onOpenChange={setToolDrawerOpen}>
        <SheetContent side="right" className="w-full overflow-y-auto sm:max-w-md">
          <SheetHeader>
            <SheetTitle>{CHAT_COPY.toolDrawer.title}</SheetTitle>
            <SheetDescription>{CHAT_COPY.toolDrawer.description(selectedAgentLabel)}</SheetDescription>
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
              eyebrow={CHAT_COPY.header.eyebrow}
              title={CHAT_COPY.header.title}
              description={formatConversationLabel(currentConversationId)}
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
        onDeleteConversation={handleDeleteConversation}
      />
    </>
  );
}
