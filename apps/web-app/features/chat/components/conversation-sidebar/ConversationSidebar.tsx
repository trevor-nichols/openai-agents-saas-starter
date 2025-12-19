// File Path: features/chat/components/conversation-sidebar/ConversationSidebar.tsx
// Description: Container component that wires sidebar state into a presentational view.

'use client';

import { useCallback, useState } from 'react';

import type { ConversationListItem } from '@/types/conversations';

import { useConversationSidebarState } from '../../hooks/useConversationSidebarState';
import { RenameConversationDialog } from './RenameConversationDialog';
import { ConversationSidebarView } from './ConversationSidebarView';

export interface ConversationSidebarProps {
  conversationList: ConversationListItem[];
  isLoadingConversations: boolean;
  isFetchingMoreConversations?: boolean;
  loadMoreConversations?: () => void;
  hasNextConversationPage?: boolean;
  currentConversationId: string | null;
  onSelectConversation: (conversationId: string) => void;
  onNewConversation: () => void;
  onDeleteConversation?: (conversationId: string) => void | Promise<void>;
  onRenameConversation?: (conversationId: string, title: string) => void | Promise<void>;
  className?: string;
  variant?: 'default' | 'embedded';
}

export function ConversationSidebar({
  conversationList,
  isLoadingConversations,
  isFetchingMoreConversations,
  loadMoreConversations,
  hasNextConversationPage,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  onRenameConversation,
  className,
  variant = 'default',
}: ConversationSidebarProps) {
  const [renameTarget, setRenameTarget] = useState<{
    conversationId: string;
    currentTitle: string;
  } | null>(null);
  const [isRenaming, setIsRenaming] = useState(false);

  const {
    tab,
    setTab,
    searchTerm,
    handleSearchChange,
    clearSearch,
    groupedConversations,
    groupOrder,
    isSearching,
    isFetchingMoreSearchResults,
    showSearchEmpty,
    searchResults,
    infiniteScrollRef,
  } = useConversationSidebarState({
    conversationList,
    isLoadingConversations,
    isFetchingMoreConversations,
    loadMoreConversations,
    hasNextConversationPage,
  });

  const handleRenameRequest = useCallback(
    (conversation: ConversationListItem) => {
      if (!onRenameConversation) return;
      const currentTitle = conversation.display_name ?? conversation.title ?? '';
      setRenameTarget({ conversationId: conversation.id, currentTitle });
    },
    [onRenameConversation],
  );

  const handleRenameOpenChange = useCallback((open: boolean) => {
    if (!open) {
      setRenameTarget(null);
    }
  }, []);

  const handleRenameSubmit = useCallback(
    async (title: string) => {
      if (!renameTarget || !onRenameConversation) return;
      setIsRenaming(true);
      try {
        await onRenameConversation(renameTarget.conversationId, title);
        setRenameTarget(null);
      } catch {
        // Keep dialog open; caller is responsible for user-facing error handling.
      } finally {
        setIsRenaming(false);
      }
    },
    [onRenameConversation, renameTarget],
  );

  return (
    <>
      <ConversationSidebarView
        variant={variant}
        className={className}
        tab={tab}
        onTabChange={setTab}
        searchTerm={searchTerm}
        onSearchChange={handleSearchChange}
        onClearSearch={clearSearch}
        showTabs={Boolean(searchTerm)}
        groupedConversations={groupedConversations}
        groupOrder={groupOrder}
        recentLoading={isLoadingConversations}
        recentFetchingMore={Boolean(isFetchingMoreConversations)}
        recentCount={conversationList.length}
        searchResults={searchResults}
        isSearching={isSearching}
        isFetchingMoreSearchResults={isFetchingMoreSearchResults}
        showSearchEmpty={showSearchEmpty}
        currentConversationId={currentConversationId}
        onSelectConversation={onSelectConversation}
        onDeleteConversation={onDeleteConversation}
        onRenameConversation={onRenameConversation ? handleRenameRequest : undefined}
        onNewConversation={onNewConversation}
        infiniteScrollRef={infiniteScrollRef}
      />

      <RenameConversationDialog
        key={renameTarget?.conversationId ?? 'closed'}
        open={renameTarget !== null}
        conversationTitle={renameTarget?.currentTitle ?? ''}
        isSubmitting={isRenaming}
        onOpenChange={handleRenameOpenChange}
        onSubmit={handleRenameSubmit}
      />
    </>
  );
}
