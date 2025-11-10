// File Path: app/(agent)/page.tsx
// Description: Main page for agent interactions. It orchestrates the ChatInterface
// and ConversationSidebar components, using custom hooks for data management.
// Dependencies:
// - React: For component structure and state management.
// - ./actions: For streamChatAgent Server Action.
// - ../../components/agent/ChatInterface: For rendering the chat UI.
// - ../../components/agent/ConversationSidebar: For rendering the conversation list.
// - ../../hooks/useConversations: For managing conversation list state and logic.
// - Tailwind CSS: For styling.
// - app/(agent)/layout.tsx: This page is wrapped by the AgentLayout.
// Dependents:
// - None directly, but orchestrates child components.

'use client';

import React, { useState, useCallback } from 'react';
import type { ConversationListItem } from '@/types/conversations';
import type { ConversationHistory, ConversationMessage } from '@/types/conversations';
import { streamChat } from '@/lib/api/streaming';
import ChatInterface, { ChatMessage } from '../../components/agent/ChatInterface';
import ConversationSidebar from '../../components/agent/ConversationSidebar';
import BillingEventsPanel from '../../components/billing/BillingEventsPanel';
import { useAgents } from '@/lib/queries/agents';
import { useConversations } from '@/lib/queries/conversations';
import { useBillingStream } from '@/lib/queries/billing';
import { useSendChatMutation } from '@/lib/queries/chat';
import { deleteConversationById, fetchConversationHistory } from '@/lib/api/conversations';

// --- AgentPage Component (Container) ---
export default function AgentPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [isClearingConversation, setIsClearingConversation] = useState(false);

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
  const sendChatMutation = useSendChatMutation();

  const mapHistoryToChatMessages = useCallback((history: ConversationHistory): ChatMessage[] => {
    return history.messages
      .filter((message: ConversationMessage) => message.role !== 'system' || message.content.trim().length > 0)
      .map((message: ConversationMessage, index: number) => {
        const normalizedRole: ChatMessage['role'] = message.role === 'user' ? 'user' : 'assistant';
        const content =
          message.role === 'system' ? `[system] ${message.content}` : message.content;
        return {
          id: message.timestamp ?? `${normalizedRole}-${history.conversation_id}-${index}`,
          role: normalizedRole,
          content,
          timestamp: message.timestamp ?? undefined,
        };
      });
  }, []);

  // Function to fetch messages for a selected conversation
  const loadMessagesForConversation = useCallback(
    async (conversationId: string) => {
      console.log(`[Client AgentPage] Loading messages for conversation: ${conversationId}`);
      setIsLoadingHistory(true);
      setMessages([]);
      try {
        const history = await fetchConversationHistory(conversationId);
        setCurrentConversationId(history.conversation_id);
        setMessages(mapHistoryToChatMessages(history));
      } catch (error) {
        console.error('[Client AgentPage] Failed to load conversation history:', error);
        alert(
          `Unable to load conversation history: ${
            error instanceof Error ? error.message : 'Unknown error'
          }`,
        );
      } finally {
        setIsLoadingHistory(false);
      }
    },
    [mapHistoryToChatMessages],
  );

  const handleSelectConversation = (conversationId: string) => {
    if (conversationId === currentConversationId) return;
    setCurrentConversationId(conversationId);
    void loadMessagesForConversation(conversationId);
  };

  const handleNewConversation = () => {
    console.log("[Client AgentPage] Starting new conversation");
    setCurrentConversationId(null); // Clear current conversation ID
    setMessages([]); // Clear messages from the UI
    setIsLoadingHistory(false);
    // Optionally, you could create a new conversation on the backend here if desired,
    // or let the first message create it.
  };

  const handleSendMessage = async (messageText: string) => {
    if (!messageText.trim() || isSending || isLoadingHistory) return;

    setIsSending(true);

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: messageText,
      timestamp: new Date().toISOString(),
    };
    setMessages(prevMessages => [...prevMessages, userMessage]);

    const assistantMessageId = `assistant-${Date.now()}`;
    const assistantPlaceholderMessage: ChatMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: "▋", // Unicode block character for typing indicator
      timestamp: new Date().toISOString(),
      isStreaming: true,
    };
    setMessages(prevMessages => [...prevMessages, assistantPlaceholderMessage]);

    const tempConversationId = currentConversationId; // Capture state at this point

    try {
      const stream = streamChat({
        message: messageText,
        conversationId: tempConversationId,
        // agentType: selectedAgent, // TODO: Add agent selection later
      });

      let accumulatedContent = "";
      let finalConversationIdFromStream: string | null = null;

      for await (const chunk of stream) {
        if (chunk.type === 'content') {
          accumulatedContent += chunk.payload;
          setMessages(prevMessages =>
            prevMessages.map(msg =>
              msg.id === assistantMessageId
                ? { ...msg, content: accumulatedContent + "▋", isStreaming: true }
                : msg
            )
          );
          if (chunk.conversationId) {
            finalConversationIdFromStream = chunk.conversationId; 
          }
        } else if (chunk.type === 'error') {
          console.error("[Client] Stream error:", chunk.payload);
          setMessages(prevMessages =>
            prevMessages.map(msg =>
              msg.id === assistantMessageId
                ? { ...msg, content: `Error: ${chunk.payload}`, isStreaming: false }
                : msg
            )
          );
          break;
        }
      }

      setMessages(prevMessages =>
        prevMessages.map(msg =>
          msg.id === assistantMessageId
            ? { ...msg, content: accumulatedContent, isStreaming: false }
            : msg
        )
      );
      
      if (finalConversationIdFromStream) {
        const summary = messageText.substring(0, 50) + (messageText.length > 50 ? "..." : "");
        const catalogItem: ConversationListItem = {
          id: finalConversationIdFromStream,
          last_message_summary: summary,
          updated_at: new Date().toISOString(),
        };

        if (!tempConversationId) {
          setCurrentConversationId(finalConversationIdFromStream);
          addConversationToList(catalogItem);
          console.log("[Client] New conversation started, ID:", finalConversationIdFromStream);
        } else if (finalConversationIdFromStream === tempConversationId) {
          updateConversationInList(catalogItem);
          console.log("[Client] Existing conversation updated, ID:", tempConversationId);
        }

      }

    } catch (error) {
      console.error("[Client] Error in handleSendMessage:", error);
      try {
        const fallbackResponse = await sendChatMutation.mutateAsync({
          message: messageText,
          conversation_id: tempConversationId ?? undefined,
          agent_type: 'triage',
          context: null,
        });

        setMessages(prevMessages =>
          prevMessages.map(msg =>
            msg.id === assistantMessageId
              ? { ...msg, content: fallbackResponse.response, isStreaming: false }
              : msg
          )
        );

        const fallbackConversationId = fallbackResponse.conversation_id;
        if (fallbackConversationId) {
          const summary = messageText.substring(0, 50) + (messageText.length > 50 ? "..." : "");
          const listItem: ConversationListItem = {
            id: fallbackConversationId,
            last_message_summary: summary,
            updated_at: new Date().toISOString(),
          };

          if (!tempConversationId || tempConversationId !== fallbackConversationId) {
            setCurrentConversationId(fallbackConversationId);
            addConversationToList(listItem);
          } else {
            updateConversationInList(listItem);
          }
        }
      } catch (fallbackError) {
        console.error('[Client] Fallback send failed:', fallbackError);
        setMessages(prevMessages =>
          prevMessages
            .filter(msg => msg.id !== assistantMessageId)
            .map(msg =>
              msg.id === userMessage.id
                ? { ...msg, content: `${msg.content} (Error sending)` }
                : msg
            )
        );
        alert(
          `An unexpected error occurred: ${
            fallbackError instanceof Error ? fallbackError.message : "Unknown error"
          }`
        );
      }
    } finally {
      setIsSending(false);
    }
  };

  const handleDeleteConversation = useCallback(
    async (conversationId: string) => {
      if (!conversationId || isClearingConversation) {
        return;
      }

      const shouldDelete =
        typeof window === 'undefined' ? true : window.confirm('Delete this conversation permanently?');
      if (!shouldDelete) {
        return;
      }

      setIsClearingConversation(true);
      try {
        await deleteConversationById(conversationId);
        removeConversationFromList(conversationId);
        loadConversations();
        if (currentConversationId === conversationId) {
          setCurrentConversationId(null);
          setMessages([]);
        }
      } catch (error) {
        console.error('[Client AgentPage] Failed to delete conversation:', error);
        alert(
          `Failed to delete conversation: ${
            error instanceof Error ? error.message : 'Unknown error'
          }`,
        );
      } finally {
        setIsClearingConversation(false);
      }
    },
    [
      currentConversationId,
      isClearingConversation,
      loadConversations,
      removeConversationFromList,
    ],
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
            onSendMessage={handleSendMessage}
            isSending={isSending}
            currentConversationId={currentConversationId}
            onClearConversation={
              currentConversationId ? () => handleDeleteConversation(currentConversationId) : undefined
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
