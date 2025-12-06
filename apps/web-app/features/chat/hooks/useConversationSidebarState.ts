import { useCallback, useEffect, useMemo, useState } from 'react';

import { useConversationSearch } from '@/lib/queries/conversations';
import type { ConversationListItem } from '@/types/conversations';

import { DATE_GROUP_ORDER, groupConversationsByDate, mapSearchResultsToListItems } from '../utils/conversationGrouping';
import { useInfiniteScroll } from './useInfiniteScroll';

export type ConversationSidebarTab = 'recent' | 'search';

interface SidebarStateParams {
  conversationList: ConversationListItem[];
  isLoadingConversations: boolean;
  loadMoreConversations?: () => void;
  hasNextConversationPage?: boolean;
}

export function useConversationSidebarState({
  conversationList,
  isLoadingConversations,
  loadMoreConversations,
  hasNextConversationPage,
}: SidebarStateParams) {
  const [tab, setTab] = useState<ConversationSidebarTab>('recent');
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');

  // Debounce search input
  useEffect(() => {
    const id = setTimeout(() => setDebouncedSearch(searchTerm.trim()), 250);
    return () => clearTimeout(id);
  }, [searchTerm]);

  const handleSearchChange = useCallback((value: string) => {
    setSearchTerm(value);
    if (value && tab !== 'search') {
      setTab('search');
    } else if (!value && tab === 'search') {
      setTab('recent');
    }
  }, [tab]);

  const clearSearch = useCallback(() => {
    setSearchTerm('');
    setTab('recent');
  }, []);

  const {
    results: rawSearchResults,
    isLoading: isSearching,
    loadMore: loadMoreSearch,
    hasNextPage: hasNextSearchPage,
  } = useConversationSearch(debouncedSearch);

  const searchResults = useMemo(
    () => mapSearchResultsToListItems(rawSearchResults),
    [rawSearchResults],
  );

  const groupedConversations = useMemo(
    () => groupConversationsByDate(conversationList),
    [conversationList],
  );

  const showSearchEmpty = !!debouncedSearch && !isSearching && searchResults.length === 0;

  const infiniteScrollRef = useInfiniteScroll({
    loadMore: tab === 'recent' ? loadMoreConversations : loadMoreSearch,
    hasNextPage: tab === 'recent' ? hasNextConversationPage : hasNextSearchPage,
    isLoading: tab === 'recent' ? isLoadingConversations : isSearching,
  });

  return {
    tab,
    setTab,
    searchTerm,
    handleSearchChange,
    clearSearch,
    groupedConversations,
    groupOrder: DATE_GROUP_ORDER,
    isSearching,
    showSearchEmpty,
    searchResults,
    infiniteScrollRef,
  };
}
