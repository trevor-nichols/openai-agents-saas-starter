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
import { ConversationListItem } from '../../app/(agent)/actions'; // Assuming ConversationListItem is exported from actions

interface ConversationSidebarProps {
  conversationList: ConversationListItem[];
  isLoadingConversations: boolean;
  currentConversationId: string | null;
  onSelectConversation: (conversationId: string) => void;
  onNewConversation: () => void; // Function to handle new conversation creation
}

export default function ConversationSidebar({
  conversationList,
  isLoadingConversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
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
                <button
                  onClick={() => onSelectConversation(conv.id)}
                  className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors duration-150
                    ${
                      currentConversationId === conv.id
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                    }`}
                >
                  <p className="font-medium truncate">
                    {conv.title || (conv.id ? conv.id.substring(0, 12) + "..." : "Unknown conversation")}
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
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  );
} 