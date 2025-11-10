// File Path: app/(agent)/page.tsx
// Description: Main page for agent interactions. It orchestrates the ChatInterface
// and ConversationSidebar components, using custom hooks for data management.
// Dependencies:
// - React: For component structure and state management.
// - ./actions: For streamChatAgent Server Action.
// - ../../components/agent/ChatInterface: For rendering the chat UI.
// - ../../components/agent/ConversationSidebar: For rendering the conversation list.
// - useChatController: Encapsulated chat orchestration (streaming, mutations, errors).
// - Tailwind CSS: For styling.
// - app/(agent)/layout.tsx: This page is wrapped by the AgentLayout.
// Dependents:
// - None directly, but orchestrates child components.

'use client';

import React, { useCallback } from 'react';
import ChatInterface from '../../components/agent/ChatInterface';
import ConversationSidebar from '../../components/agent/ConversationSidebar';
import BillingEventsPanel from '../../components/billing/BillingEventsPanel';
import { useAgents } from '@/lib/queries/agents';
import { useConversations } from '@/lib/queries/conversations';
import { useBillingStream } from '@/lib/queries/billing';
import { useChatController } from '@/lib/chat/useChatController';

// --- AgentPage Component (Container) ---
export default function AgentPage() {
  const {
    conversationList,
    isLoadingConversations,
    addConversationToList,
    updateConversationInList,
    removeConversationFromList,
    loadConversations,
  } = useConversations();
  const { events: billingEvents, status: billingStreamStatus } = useBillingStream();
  const {
    agents,
    isLoadingAgents,
    agentsError,
  } = useAgents();
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
    <div className="flex flex-col h-screen max-h-screen bg-background text-foreground p-4 sm:p-6 md:p-8">
      <header className="mb-6 flex-shrink-0">
        <h1 className="text-3xl sm:text-4xl font-bold text-center sm:text-left">Anything Agent Chat</h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 text-center sm:text-left mt-1">
          {currentConversationId ? `Conversation ID: ${currentConversationId.substring(0, 12)}...` : "Start a new conversation."}
        </p>
        <p className="text-xs text-gray-500 dark:text-gray-400 text-center sm:text-left mt-1">
          {isLoadingAgents
            ? 'Loading agent inventory…'
            : agentsError
              ? `Agent inventory unavailable: ${agentsError.message}`
              : agents.length > 0
                ? `${agents.length} agents available · ${agents.filter(agent => agent.status === 'active').length} active`
                : 'No agents registered.'}
        </p>
      </header>

      {errorMessage && (
        <div className="mb-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {errorMessage}
        </div>
      )}

      <main className="flex-grow flex flex-col md:flex-row gap-6 overflow-hidden">
        <ConversationSidebar
          conversationList={conversationList}
          isLoadingConversations={isLoadingConversations}
          currentConversationId={currentConversationId}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
          onDeleteConversation={handleDeleteConversation}
        />

        <div className="w-full md:w-3/4 lg:w-4/5 flex flex-col h-full">
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
      </main>

      <footer className="flex-shrink-0 mt-6 text-center text-xs text-gray-500 dark:text-gray-400">
        <p>&copy; {new Date().getFullYear()} Anything Agents. All rights reserved.</p>
      </footer>
    </div>
  );
}
