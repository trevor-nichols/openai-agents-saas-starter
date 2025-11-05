// File Path: hooks/useConversations.ts
// Description: This custom hook manages the state and fetching logic for the conversation list.
// It encapsulates the interaction with the listConversationsAction server action.
// Dependencies:
// - React: For useState, useEffect, useCallback.
// - ../app/(agent)/actions: For listConversationsAction and ConversationListItem type.
// Dependents:
// - app/(agent)/page.tsx: This hook will be used to provide conversation data and loading states.

import { useState, useEffect, useCallback } from 'react';
import { listConversationsAction, ConversationListItem } from '../app/(agent)/actions';

interface UseConversationsReturn {
  conversationList: ConversationListItem[];
  isLoadingConversations: boolean;
  loadConversations: () => Promise<void>;
  error: string | null;
  addConversationToList: (newConversation: ConversationListItem) => void;
  updateConversationInList: (updatedConversation: ConversationListItem) => void;
}

export function useConversations(): UseConversationsReturn {
  const [conversationList, setConversationList] = useState<ConversationListItem[]>([]);
  const [isLoadingConversations, setIsLoadingConversations] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadConversations = useCallback(async () => {
    console.log("[useConversations] Fetching conversation list...");
    setIsLoadingConversations(true);
    setError(null);
    try {
      const result = await listConversationsAction();
      if (result.success && result.conversations) {
        setConversationList(result.conversations);
        console.log("[useConversations] Conversation list loaded:", result.conversations.length);
      } else {
        console.error("[useConversations] Failed to load conversations:", result.error);
        setError(result.error || 'Unknown error loading conversations');
        alert(`Error loading conversations: ${result.error || 'Unknown error'}`);
      }
    } catch (error: unknown) {
      console.error("[useConversations] Exception while loading conversations:", error);
      setError(error instanceof Error ? error.message : 'An unexpected error occurred');
      alert(`Exception loading conversations: ${error instanceof Error ? error.message : 'An unexpected error occurred'}`);
    }
    setIsLoadingConversations(false);
  }, []);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  const addConversationToList = (newConversation: ConversationListItem) => {
    setConversationList(prevList => {
        // Avoid adding if it already exists, or prepend if it's new
        if (prevList.find(c => c.id === newConversation.id)) {
            return prevList.map(c => c.id === newConversation.id ? newConversation : c).sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
        }
        return [newConversation, ...prevList].sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
    });
  };

  const updateConversationInList = (updatedConversation: ConversationListItem) => {
    setConversationList(prevList => 
        prevList.map(c => c.id === updatedConversation.id ? updatedConversation : c)
                .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
    );
  };

  return { conversationList, isLoadingConversations, loadConversations, error, addConversationToList, updateConversationInList };
} 