// File Path: app/(app)/(workspace)/chat/page.tsx
// Description: Chat workspace page composed within the authenticated app shell.
// Sections:
// - Imports: UI components and hooks enabling the chat experience.
// - Event handlers: Stable callbacks for conversation management.
// - ChatWorkspace component: Orchestrates sidebar, chat interface, and billing events panel.

'use client';

import React, { useCallback } from 'react';

import ChatInterface from '../../../../components/agent/ChatInterface';
import ConversationSidebar from '../../../../components/agent/ConversationSidebar';
import BillingEventsPanel from '../../../../components/billing/BillingEventsPanel';
import { useAgents } from '@/lib/queries/agents';
import { useConversations } from '@/lib/queries/conversations';
import { useBillingStream } from '@/lib/queries/billing';
import { useChatController } from '@/lib/chat/useChatController';

export default function ChatWorkspacePage() {
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
        typeof window === 'undefined'
          ? true
          : window.confirm('Delete this conversation permanently?');
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
          <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {errorMessage}
          </div>
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

