// File Path: features/chat/components/ConversationSidebar.tsx
// Description: Glass-styled sidebar for managing conversations with professional UI/UX.

'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { Plus, Search, Trash2, MessageSquare, MoreVertical, History, Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { GlassPanel } from '@/components/ui/foundation';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';
import type { ConversationListItem } from '@/types/conversations';
import { useConversationSearch } from '@/lib/queries/conversations';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface ConversationSidebarProps {
  conversationList: ConversationListItem[];
  isLoadingConversations: boolean;
  loadMoreConversations?: () => void;
  hasNextConversationPage?: boolean;
  currentConversationId: string | null;
  onSelectConversation: (conversationId: string) => void;
  onNewConversation: () => void;
  onDeleteConversation?: (conversationId: string) => void | Promise<void>;
  className?: string;
}

type DateGroup = 'Today' | 'Yesterday' | 'Previous 7 Days' | 'Previous 30 Days' | 'Older';

function getGroup(dateStr: string): DateGroup {
  const date = new Date(dateStr);
  const now = new Date();
  const diffTime = Math.abs(now.getTime() - date.getTime());
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)); 

  if (diffDays <= 1 && now.getDate() === date.getDate()) return 'Today';
  if (diffDays <= 2) return 'Yesterday';
  if (diffDays <= 7) return 'Previous 7 Days';
  if (diffDays <= 30) return 'Previous 30 Days';
  return 'Older';
}

function useInfiniteScroll(
  loadMore: (() => void) | undefined,
  hasNextPage: boolean | undefined,
  isLoading: boolean
) {
  const observerRef = useRef<HTMLDivElement>(null);

  const handleObserver = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      const [target] = entries;
      if (target?.isIntersecting && hasNextPage && !isLoading && loadMore) {
        loadMore();
      }
    },
    [loadMore, hasNextPage, isLoading]
  );

  useEffect(() => {
    const element = observerRef.current;
    if (!element) return;

    const observer = new IntersectionObserver(handleObserver, {
      root: null,
      rootMargin: '20px',
      threshold: 0,
    });

    observer.observe(element);
    return () => observer.disconnect();
  }, [handleObserver]);

  return observerRef;
}

export function ConversationSidebar({
  conversationList,
  isLoadingConversations,
  currentConversationId,
  loadMoreConversations,
  hasNextConversationPage,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  className,
  variant = 'default',
}: ConversationSidebarProps & { variant?: 'default' | 'embedded' }) {
  const [tab, setTab] = useState<'recent' | 'search'>('recent');
  const [searchTerm, setSearchTerm] = useState('');
  const [debounced, setDebounced] = useState('');

  useEffect(() => {
    const id = setTimeout(() => setDebounced(searchTerm.trim()), 250);
    return () => clearTimeout(id);
  }, [searchTerm]);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchTerm(value);
    
    if (value && tab !== 'search') {
      setTab('search');
    } else if (!value && tab === 'search') {
      setTab('recent');
    }
  };

  const {
    results: searchResults,
    isLoading: isSearching,
    loadMore: loadMoreSearch,
    hasNextPage: hasNextSearchPage,
  } = useConversationSearch(debounced);

  // True when a debounced search has no hits and loading finished
  const showSearchEmpty = !!debounced && !isSearching && searchResults.length === 0;

  // Grouping Logic
  const groupedConversations = conversationList.reduce((groups, conversation) => {
    const group = getGroup(conversation.updated_at);
    if (!groups[group]) groups[group] = [];
    groups[group].push(conversation);
    return groups;
  }, {} as Record<DateGroup, ConversationListItem[]>);

  const groupOrder: DateGroup[] = ['Today', 'Yesterday', 'Previous 7 Days', 'Previous 30 Days', 'Older'];

  const infiniteScrollRef = useInfiniteScroll(
    tab === 'recent' ? loadMoreConversations : loadMoreSearch,
    tab === 'recent' ? hasNextConversationPage : hasNextSearchPage,
    tab === 'recent' ? isLoadingConversations : isSearching
  );

  const renderList = (items: ConversationListItem[], loading: boolean, isSearch = false, isEmptySearch = false) => {
    if (loading && items.length === 0) {
      return (
        <div className="space-y-4 px-2 pt-2">
          {Array.from({ length: 5 }).map((_, index) => (
            <div key={index} className="flex flex-col gap-2">
              <div className="h-4 w-3/4 animate-pulse rounded bg-muted/20" />
              <div className="h-3 w-1/2 animate-pulse rounded bg-muted/10" />
            </div>
          ))}
        </div>
      );
    }

    if (isEmptySearch) {
      return (
        <div className="flex flex-col items-center justify-center py-10 px-4 text-center text-muted-foreground">
          <p className="text-sm">No matches found.</p>
          <Button variant="link" size="sm" onClick={() => setSearchTerm('')} className="mt-2 h-auto p-0 text-xs">
            Clear search
          </Button>
        </div>
      );
    }

    if (!items.length) {
      return (
        <div className="flex flex-col items-center justify-center py-10 px-4 text-center text-muted-foreground">
          <MessageSquare className="mb-2 h-8 w-8 opacity-20" />
          <p className="text-sm">No conversations</p>
          {!isSearch && (
            <Button variant="link" size="sm" onClick={onNewConversation} className="mt-2 h-auto p-0 text-xs">
              Start a new chat
            </Button>
          )}
        </div>
      );
    }

    // If searching, just list them flat. If recent, group them.
    if (isSearch) {
      return (
        <ul className="space-y-1 px-2">
          {items.map((conv) => (
            <ConversationItem
              key={conv.id}
              conversation={conv}
              isActive={currentConversationId === conv.id}
              onSelect={() => onSelectConversation(conv.id)}
              onDelete={onDeleteConversation ? () => onDeleteConversation(conv.id) : undefined}
            />
          ))}
        </ul>
      );
    }

    return (
      <div className="space-y-6 px-2">
        {groupOrder.map((group) => {
          const groupItems = groupedConversations[group];
          if (!groupItems?.length) return null;

          return (
            <div key={group}>
              <h3 className="mb-2 px-2 text-[10px] font-medium uppercase tracking-wider text-muted-foreground/50">
                {group}
              </h3>
              <ul className="space-y-0.5">
                {groupItems.map((conv) => (
                  <ConversationItem
                    key={conv.id}
                    conversation={conv}
                    isActive={currentConversationId === conv.id}
                    onSelect={() => onSelectConversation(conv.id)}
                    onDelete={onDeleteConversation ? () => onDeleteConversation(conv.id) : undefined}
                  />
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    );
  };

  const Content = (
    <>
      {/* Header Section */}
      <div className="flex flex-col gap-4 p-4 pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-muted-foreground">
            <History className="h-4 w-4" />
            <h2 className="text-sm font-medium">History</h2>
          </div>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  onClick={onNewConversation}
                  size="icon"
                  variant="ghost"
                  className="h-8 w-8 rounded-full hover:bg-primary/10 hover:text-primary"
                >
                  <Plus className="h-4 w-4" />
                  <span className="sr-only">New Chat</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">New Conversation</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>

        {/* Search Input */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground/50" />
          <Input
            placeholder="Search chats..."
            value={searchTerm}
            onChange={handleSearchChange}
            className="h-9 rounded-lg border-transparent bg-muted/50 pl-9 text-sm focus-visible:bg-background focus-visible:ring-1"
          />
        </div>
      </div>

      {/* Tabs & List */}
      <Tabs
        value={tab}
        onValueChange={(value) => setTab(value as 'recent' | 'search')}
        className="flex flex-1 flex-col overflow-hidden"
      >
        {searchTerm && (
          <div className="px-4 pb-2">
            <TabsList className="grid w-full grid-cols-2 bg-muted/30 p-0.5 h-8">
              <TabsTrigger value="recent" className="h-7 text-xs">Recent</TabsTrigger>
              <TabsTrigger value="search" className="h-7 text-xs">Results</TabsTrigger>
            </TabsList>
          </div>
        )}

        <ScrollArea className="flex-1">
          {/* We use w-full max-w-full min-w-0 to enforce strict width constraint on the scroll content */}
          <div className="flex flex-col py-2 w-full max-w-full min-w-0">
            {tab === 'recent' 
              ? renderList(conversationList, isLoadingConversations) 
              : renderList(
                  searchResults.map((hit) => ({
                    id: hit.conversation_id,
                    title: hit.topic_hint ?? hit.preview,
                    topic_hint: hit.topic_hint,
                    agent_entrypoint: hit.agent_entrypoint,
                    active_agent: hit.active_agent,
                    last_message_preview: hit.last_message_preview ?? hit.preview,
                    updated_at: hit.updated_at ?? new Date().toISOString(),
                  })),
                  isSearching,
                  true,
                  showSearchEmpty
                )
            }
            
            {/* Infinite Scroll Trigger */}
            <div ref={infiniteScrollRef} className="flex justify-center py-4">
              {(tab === 'recent' ? isLoadingConversations : isSearching) && (conversationList.length > 0 || searchResults.length > 0) && (
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
              )}
            </div>
          </div>
        </ScrollArea>
      </Tabs>
    </>
  );

  if (variant === 'embedded') {
    return <div className={cn('flex h-full w-full flex-col overflow-hidden', className)}>{Content}</div>;
  }

  return (
    <GlassPanel className={cn('flex h-full w-full flex-col overflow-hidden bg-background/40 backdrop-blur-xl border-r', className)}>
      {Content}
    </GlassPanel>
  );
}

function ConversationItem({
  conversation,
  isActive,
  onSelect,
  onDelete,
}: {
  conversation: ConversationListItem;
  isActive: boolean;
  onSelect: () => void;
  onDelete?: () => void;
}) {
  const title =
    conversation.title?.trim() ||
    conversation.topic_hint?.trim() ||
    `New Conversation`;

  return (
    <li className="group relative w-full min-w-0">
      <button
        type="button"
        onClick={onSelect}
        className={cn(
          'grid w-full grid-cols-1 gap-0.5 rounded-lg px-3 py-2.5 text-left transition-all duration-200',
          isActive
            ? 'bg-muted font-medium text-foreground'
            : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
        )}
      >
        <span className="truncate text-sm leading-tight block">{title}</span>
        <span className="truncate text-xs text-muted-foreground/60 font-normal block">
          {conversation.last_message_preview || 'No messages'}
        </span>
      </button>

      {onDelete && (
        <div
          className={cn(
            'absolute right-1 top-1/2 -translate-y-1/2 opacity-0 transition-opacity duration-200 group-hover:opacity-100',
            isActive && 'opacity-100'
          )}
        >
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 rounded-md hover:bg-background/80"
                onClick={(e) => e.stopPropagation()}
              >
                <MoreVertical className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="sr-only">Options</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                className="text-destructive focus:text-destructive"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete();
                }}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      )}
    </li>
  );
}
