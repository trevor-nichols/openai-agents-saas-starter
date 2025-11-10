// File Path: features/chat/components/ConversationSidebar.tsx
// Description: Sidebar listing conversations with quick actions.
// Sections:
// - Props: Conversation data and callbacks provided by the chat orchestrator.
// - UI: Header actions, conversation list, logout control.

'use client';

import React from 'react';

import type { ConversationListItem } from '@/types/conversations';

import { LogoutButton } from '@/components/auth/LogoutButton';

interface ConversationSidebarProps {
  conversationList: ConversationListItem[];
  isLoadingConversations: boolean;
  currentConversationId: string | null;
  onSelectConversation: (conversationId: string) => void;
  onNewConversation: () => void;
  onDeleteConversation?: (conversationId: string) => void | Promise<void>;
}

export function ConversationSidebar({
  conversationList,
  isLoadingConversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
}: ConversationSidebarProps) {
  return (
    <aside className="flex w-full flex-shrink-0 flex-col rounded-lg bg-gray-100 p-4 shadow dark:bg-gray-800 md:w-1/4 lg:w-1/5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xl font-semibold">Conversations</h2>
        <button
          onClick={onNewConversation}
          className="rounded-md bg-blue-500 px-3 py-1.5 text-sm text-white transition hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-400"
        >
          New
        </button>
      </div>

      <div className="flex-grow overflow-y-auto">
        {isLoadingConversations ? (
          <p className="text-sm text-gray-500 dark:text-gray-400">Loading conversations...</p>
        ) : conversationList.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400">No conversations yet. Start a new one!</p>
        ) : (
          <ul className="space-y-2">
            {conversationList
              .filter((conversation) => conversation && conversation.id)
              .map((conversation) => (
                <li key={conversation.id}>
                  <div
                    className={`group flex items-start justify-between gap-2 rounded-md px-3 py-2 text-sm transition-colors duration-150 ${
                      currentConversationId === conversation.id
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-700 hover:bg-gray-200 dark:text-gray-300 dark:hover:bg-gray-700'
                    }`}
                  >
                    <button
                      type="button"
                      onClick={() => onSelectConversation(conversation.id)}
                      className="flex-1 text-left focus:outline-none"
                    >
                      <p className="truncate font-medium">
                        {conversation.title ||
                          (conversation.id ? `${conversation.id.substring(0, 12)}...` : 'Unknown conversation')}
                      </p>
                      {conversation.last_message_summary ? (
                        <p className="mt-0.5 truncate text-xs text-gray-500 dark:text-gray-400">
                          {conversation.last_message_summary}
                        </p>
                      ) : null}
                      <p className="mt-1 text-xs text-gray-400 dark:text-gray-500">
                        {new Date(conversation.updated_at).toLocaleDateString()}
                      </p>
                    </button>
                    {onDeleteConversation ? (
                      <button
                        type="button"
                        onClick={(event) => {
                          event.stopPropagation();
                          onDeleteConversation(conversation.id);
                        }}
                        className={`rounded border px-2 py-1 text-xs font-medium ${
                          currentConversationId === conversation.id
                            ? 'border-white text-white hover:bg-white hover:text-blue-600'
                            : 'border-gray-300 text-gray-600 hover:bg-gray-300 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-600'
                        }`}
                      >
                        Clear
                      </button>
                    ) : null}
                  </div>
                </li>
              ))}
          </ul>
        )}
      </div>

      <div className="mt-4 border-t border-gray-200 pt-4">
        <LogoutButton />
      </div>
    </aside>
  );
}

