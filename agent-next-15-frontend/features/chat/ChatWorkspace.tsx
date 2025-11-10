// File Path: features/chat/ChatWorkspace.tsx
// Description: Client-side orchestrator for the chat workspace.
// Sections:
// - Data hooks: Conversations, billing stream, agent inventory.
// - Event handlers: Select/new/delete conversations, message sending.
// - Layout: Sidebar + chat body + billing events panel.

'use client';

import React, { useCallback } from 'react';

import { BillingEventsPanel } from './components/BillingEventsPanel';
import { ChatInterface } from './components/ChatInterface';
import { ConversationSidebar } from './components/ConversationSidebar';
import { useChatController } from '@/lib/chat/useChatController';
import { useBillingStream } from '@/lib/queries/billing';
import { useConversations } from '@/lib/queries/conversations';
import { useAgents } from '@/lib/queries/agents';

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

  return (
    <div className="flex flex-1 flex-col gap-6 lg:flex-row">
      <ConversationSidebar
        conversationList={conversationList}
        isLoadingConversations={isLoadingConversations}
        currentConversationId={currentConversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        onDeleteConversation={handleDeleteConversation}
      />

      <div className="flex w-full flex-1 flex-col gap-6">
        <header className="space-y-2">
          <h1 className="text-2xl font-semibold text-slate-900">Anything Agent Chat</h1>
          <p className="text-sm text-slate-500">
            {currentConversationId
              ? `Conversation ID: ${currentConversationId.substring(0, 12)}…`
              : 'Start a new conversation.'}
          </p>
          <p className="text-xs text-slate-400">
            {isLoadingAgents
              ? 'Loading agent inventory…'
              : agentsError
                ? `Agent inventory unavailable: ${agentsError.message}`
                : agents.length > 0
                  ? `${agents.length} agents available · ${agents.filter((agent) => agent.status === 'active').length} active`
                  : 'No agents registered.'}
          </p>
        </header>

        {errorMessage ? (
          <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{errorMessage}</div>
        ) : null}

        <div className="flex flex-1 flex-col gap-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
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
          />
          <BillingEventsPanel events={billingEvents} status={billingStreamStatus} />
        </div>
      </div>
    </div>
  );
}

