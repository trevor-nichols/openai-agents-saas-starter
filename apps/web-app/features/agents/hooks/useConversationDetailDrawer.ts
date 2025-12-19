import { useCallback, useState } from 'react';

import type { UseChatControllerReturn } from '@/lib/chat';

interface UseConversationDetailDrawerArgs {
  chatController: UseChatControllerReturn;
  loadConversations: () => void;
}

interface ConversationDetailDrawerState {
  detailDrawerOpen: boolean;
  detailConversationId: string | null;
  setDetailDrawerOpen: (open: boolean) => void;
  openDrawerForConversation: (conversationId: string) => void;
  showCurrentConversation: () => void;
  handleConversationDeleted: (conversationId: string) => void;
}

export function useConversationDetailDrawer({
  chatController,
  loadConversations,
}: UseConversationDetailDrawerArgs): ConversationDetailDrawerState {
  const { currentConversationId, selectConversation, startNewConversation } = chatController;

  const [detailDrawerOpen, setDetailDrawerOpen] = useState(false);
  const [detailConversationId, setDetailConversationId] = useState<string | null>(null);

  const openDrawerForConversation = useCallback(
    (conversationId: string) => {
      setDetailConversationId(conversationId);
      setDetailDrawerOpen(true);
      void selectConversation(conversationId);
    },
    [selectConversation],
  );

  const showCurrentConversation = useCallback(() => {
    if (!currentConversationId) {
      return;
    }
    setDetailConversationId(currentConversationId);
    setDetailDrawerOpen(true);
  }, [currentConversationId]);

  const handleConversationDeleted = useCallback(
    (conversationId: string) => {
      loadConversations();
      if (detailConversationId === conversationId) {
        setDetailDrawerOpen(false);
        setDetailConversationId(null);
      }
      if (currentConversationId === conversationId) {
        startNewConversation();
      }
    },
    [
      currentConversationId,
      detailConversationId,
      loadConversations,
      startNewConversation,
    ],
  );

  return {
    detailDrawerOpen,
    detailConversationId,
    setDetailDrawerOpen,
    openDrawerForConversation,
    showCurrentConversation,
    handleConversationDeleted,
  };
}

