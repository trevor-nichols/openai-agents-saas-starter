// File Path: components/agent/ConversationSidebar.tsx
// Description: This component renders the sidebar displaying a list of conversations.
// It allows users to view and select conversations.
// Dependencies:
// - React: For creating the component.
// - ../../app/(agent)/actions: For the ConversationListItem type.
// - Tailwind CSS: For styling.
// Dependents:
// - app/(agent)/page.tsx: This component will be used in the main agent page layout.

'use client';

import React from 'react';

import type { ConversationListItem } from '@/types/conversations';

import { LogoutButton } from '../auth/LogoutButton';

interface ConversationSidebarProps {
  conversationList: ConversationListItem[];
  isLoadingConversations: boolean;
  currentConversationId: string | null;
  onSelectConversation: (conversationId: string) => void;
  onNewConversation: () => void; // Function to handle new conversation creation
  onDeleteConversation?: (conversationId: string) => void | Promise<void>;
}

export default function ConversationSidebar({
  conversationList,
  isLoadingConversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
}: ConversationSidebarProps) {
  return (
    <aside className="w-full md:w-1/4 lg:w-1/5 flex-shrink-0 bg-gray-100 dark:bg-gray-800 p-4 rounded-lg shadow flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Conversations</h2>
        <button
          onClick={onNewConversation}
          className="px-3 py-1.5 bg-blue-500 text-white rounded-md text-sm hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-400"
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
              .filter(conv => conv && conv.id) // Filter out any invalid conversations
              .map((conv) => (
              <li key={conv.id}>
                <div
                  className={`group flex items-start justify-between gap-2 rounded-md px-3 py-2 text-sm transition-colors duration-150 ${
                    currentConversationId === conv.id
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
                >
                  <button
                    type="button"
                    onClick={() => onSelectConversation(conv.id)}
                    className="flex-1 text-left focus:outline-none"
                  >
                    <p className="font-medium truncate">
                      {conv.title || (conv.id ? `${conv.id.substring(0, 12)}...` : 'Unknown conversation')}
                    </p>
                    {conv.last_message_summary && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 truncate mt-0.5">
                        {conv.last_message_summary}
                      </p>
                    )}
                    <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                      {new Date(conv.updated_at).toLocaleDateString()}
                    </p>
                  </button>
                  {onDeleteConversation && (
                    <button
                      type="button"
                      onClick={(event) => {
                        event.stopPropagation();
                        onDeleteConversation(conv.id);
                      }}
                      className={`text-xs font-medium px-2 py-1 rounded border ${
                        currentConversationId === conv.id
                          ? 'border-white text-white hover:bg-white hover:text-blue-600'
                          : 'border-gray-300 text-gray-600 hover:bg-gray-300 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-600'
                      }`}
                    >
                      Clear
                    </button>
                  )}
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
