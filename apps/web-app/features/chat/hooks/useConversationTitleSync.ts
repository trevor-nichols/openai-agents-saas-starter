'use client';

import { useCallback } from 'react';

import type { ConversationListItem } from '@/types/conversations';

import { useConversationTitleStream } from './useConversationTitleStream';

interface UseConversationTitleSyncOptions {
  conversationId: string | null;
  currentConversation: ConversationListItem | null;
  updateConversationInList: (updated: ConversationListItem) => void;
  getConversationBase: (conversationId: string, existing?: ConversationListItem | null) => ConversationListItem;
}

export function useConversationTitleSync({
  conversationId,
  currentConversation,
  updateConversationInList,
  getConversationBase,
}: UseConversationTitleSyncOptions) {
  const setPending = useCallback(
    (pending: boolean) => {
      if (!conversationId) return;
      const base = getConversationBase(conversationId, currentConversation);
      updateConversationInList({
        ...base,
        display_name_pending: pending,
      });
    },
    [conversationId, currentConversation, getConversationBase, updateConversationInList],
  );

  const handleTitle = useCallback(
    (title: string) => {
      if (!conversationId) return;
      const base = getConversationBase(conversationId, currentConversation);
      updateConversationInList({
        ...base,
        display_name: title,
        title,
      });
    },
    [conversationId, currentConversation, getConversationBase, updateConversationInList],
  );

  useConversationTitleStream({
    conversationId,
    onTitle: handleTitle,
    onPendingStart: () => setPending(true),
    onPendingResolve: () => setPending(false),
  });
}
