// File Path: features/chat/components/conversation-sidebar/ConversationSidebar.tsx
// Description: Container component that wires sidebar state into a presentational view.

'use client';

import type { ConversationListItem } from '@/types/conversations';

import { useConversationSidebarState } from '../../hooks/useConversationSidebarState';
import { ConversationSidebarView } from './ConversationSidebarView';

export interface ConversationSidebarProps {
  conversationList: ConversationListItem[];
  isLoadingConversations: boolean;
  loadMoreConversations?: () => void;
  hasNextConversationPage?: boolean;
  currentConversationId: string | null;
  onSelectConversation: (conversationId: string) => void;
  onNewConversation: () => void;
  onDeleteConversation?: (conversationId: string) => void | Promise<void>;
  className?: string;
  variant?: 'default' | 'embedded';
}

export function ConversationSidebar({
  conversationList,
  isLoadingConversations,
  loadMoreConversations,
  hasNextConversationPage,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  className,
  variant = 'default',
}: ConversationSidebarProps) {
  const {
    tab,
    setTab,
    searchTerm,
    handleSearchChange,
    clearSearch,
    groupedConversations,
    groupOrder,
    isSearching,
    showSearchEmpty,
    searchResults,
    infiniteScrollRef,
  } = useConversationSidebarState({
    conversationList,
    isLoadingConversations,
    loadMoreConversations,
    hasNextConversationPage,
  });

  return (
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
      recentCount={conversationList.length}
      searchResults={searchResults}
      isSearching={isSearching}
      showSearchEmpty={showSearchEmpty}
      currentConversationId={currentConversationId}
      onSelectConversation={onSelectConversation}
      onDeleteConversation={onDeleteConversation}
      onNewConversation={onNewConversation}
      infiniteScrollRef={infiniteScrollRef}
    />
  );
}
