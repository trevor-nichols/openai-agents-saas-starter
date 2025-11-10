// File Path: features/chat/components/ChatInterface.tsx
// Description: Chat transcript + composer component used inside the chat workspace.
// Sections:
// - Component props: Expected data + callbacks from the orchestrator.
// - UI: Conversation header, message list, and input form.

'use client';

import React, { useEffect, useRef, useState, type FormEvent } from 'react';

import type { ChatMessage } from '@/lib/chat/types';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  onSendMessage: (messageText: string) => Promise<void>;
  isSending: boolean;
  currentConversationId: string | null;
  onClearConversation?: () => void | Promise<void>;
  isClearingConversation?: boolean;
  isLoadingHistory?: boolean;
}

export function ChatInterface({
  messages,
  onSendMessage,
  isSending,
  currentConversationId,
  onClearConversation,
  isClearingConversation = false,
  isLoadingHistory = false,
}: ChatInterfaceProps) {
  const [messageInput, setMessageInput] = useState('');
  const chatContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const handleLocalFormSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!messageInput.trim() || isSending || isLoadingHistory) {
      return;
    }

    const textToSend = messageInput;
    setMessageInput('');
    await onSendMessage(textToSend);
  };

  return (
    <section className="flex h-full w-full flex-col overflow-hidden rounded-lg bg-white shadow dark:bg-gray-900">
      <div className="flex items-start justify-between gap-4 border-b border-gray-200 p-4 dark:border-gray-700">
        <div>
          <p className="text-sm font-semibold text-gray-800 dark:text-gray-200">
            {currentConversationId
              ? `Conversation ${currentConversationId.substring(0, 12)}...`
              : 'New conversation'}
          </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {isLoadingHistory
                ? 'Loading conversation history...'
                : currentConversationId
                  ? 'Messages loaded from history.'
                  : 'Send a message to start a new conversation.'}
            </p>
        </div>
        {onClearConversation && currentConversationId ? (
          <button
            type="button"
            onClick={() => {
              void onClearConversation();
            }}
            disabled={isClearingConversation || isLoadingHistory}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-xs font-semibold text-gray-700 transition hover:bg-gray-200 disabled:opacity-60 dark:border-gray-600 dark:text-gray-100 dark:hover:bg-gray-700"
          >
            {isClearingConversation ? 'Clearing…' : 'Clear conversation'}
          </button>
        ) : null}
      </div>

      <div
        ref={chatContainerRef}
        className="flex-grow space-y-4 overflow-y-auto border-b border-gray-200 p-4 dark:border-gray-700"
      >
        {isLoadingHistory ? (
          <div className="py-20 text-center text-gray-500 dark:text-gray-400">
            <p>Loading conversation history...</p>
          </div>
        ) : messages.length === 0 ? (
          <div className="py-20 text-center text-gray-500 dark:text-gray-400">
            <p>No messages yet.</p>
            <p className="mt-1 text-xs">Send a message to start the chat.</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-xl whitespace-pre-wrap rounded-lg px-4 py-2 shadow lg:max-w-2xl ${
                  msg.role === 'user'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                }`}
              >
                <p className="text-sm">
                  {msg.content}
                  {msg.isStreaming && msg.role === 'assistant' ? '' : ''}
                </p>
                {msg.timestamp && !msg.isStreaming ? (
                  <p
                    className={`mt-1 text-xs ${
                      msg.role === 'user' ? 'text-blue-200' : 'text-gray-500 dark:text-gray-400'
                    }`}
                  >
                    {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                ) : null}
              </div>
            </div>
          ))
        )}
      </div>

      <div className="flex-shrink-0 border-t border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-800">
        <form className="flex gap-2" onSubmit={handleLocalFormSubmit}>
          <input
            type="text"
            placeholder={`Type message${currentConversationId ? ` to ${currentConversationId.substring(0, 8)}...` : '...'}`}
            value={messageInput}
            onChange={(event) => setMessageInput(event.target.value)}
            disabled={isSending || isLoadingHistory}
            className="flex-grow rounded-lg border border-gray-300 bg-white p-3 text-foreground outline-none transition focus:border-transparent focus:ring-2 focus:ring-blue-500 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:bg-gray-700"
          />
          <button
            type="submit"
            disabled={isSending || isLoadingHistory || !messageInput.trim()}
            className="rounded-lg bg-blue-600 px-6 py-3 text-white transition-colors duration-150 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:focus:ring-offset-gray-800"
          >
            {isSending ? 'Sending...' : 'Send'}
          </button>
        </form>
      </div>
    </section>
  );
}

