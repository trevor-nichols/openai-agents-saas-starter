// File Path: features/chat/components/ConversationSidebar.tsx
// Description: Glass-styled sidebar for managing conversations with professional UI/UX.

'use client';

import { useEffect, useState } from 'react';
import { Plus, Search, Trash2, MessageSquare, MoreVertical, History } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { GlassPanel } from '@/components/ui/foundation';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';
import { formatRelativeTime } from '@/lib/utils/time';
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
import { Badge } from '@/components/ui/badge';

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
}: ConversationSidebarProps) {
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

  const showSearchEmpty = !isSearching && !searchResults.length && debounced;

  const renderList = (items: ConversationListItem[], loading: boolean) => {
    if (loading) {
      return (
        <div className="space-y-2 px-1">
          {Array.from({ length: 5 }).map((_, index) => (
            <div
              key={index}
              className="flex flex-col gap-2 rounded-lg border border-white/5 bg-white/5 p-3"
            >
              <div className="flex justify-between">
                <div className="h-4 w-24 animate-pulse rounded bg-white/10" />
                <div className="h-3 w-8 animate-pulse rounded bg-white/5" />
              </div>
              <div className="h-3 w-3/4 animate-pulse rounded bg-white/5" />
              <div className="mt-1 h-4 w-16 animate-pulse rounded-full bg-white/5" />
            </div>
          ))}
        </div>
      );
    }

    if (!items.length) {
      return (
        <div className="flex flex-col items-center justify-center py-10 px-4 text-center">
          <div className="mb-3 rounded-full bg-white/5 p-3 text-muted-foreground">
            <MessageSquare className="h-6 w-6 opacity-50" />
          </div>
          <p className="text-sm font-medium text-foreground/80">No conversations</p>
          <p className="text-xs text-muted-foreground">Get started by creating a new chat.</p>
          <Button variant="outline" size="sm" className="mt-4" onClick={onNewConversation}>
            New Chat
          </Button>
        </div>
      );
    }

    return (
      <ul className="space-y-1.5 px-1">
        {items.map((conversation) => {
          const title =
            conversation.title?.trim() ||
            conversation.topic_hint?.trim() ||
            `Conversation ${conversation.id.substring(0, 4)}`;

          const isActive = currentConversationId === conversation.id;
          const agentLabel = conversation.active_agent || conversation.agent_entrypoint;

          return (
            <li key={conversation.id} className="group relative">
              <button
                type="button"
                onClick={() => onSelectConversation(conversation.id)}
                className={cn(
                  'flex w-full flex-col gap-2 rounded-lg border p-3 text-left transition-all duration-200 ease-in-out',
                  isActive
                    ? 'border-primary/20 bg-primary/5 shadow-sm ring-1 ring-primary/10'
                    : 'border-transparent bg-transparent hover:bg-white/5 hover:text-foreground'
                )}
              >
                <div className="flex w-full items-start justify-between gap-2">
                  <span
                    className={cn(
                      'truncate text-sm font-medium leading-none',
                      isActive ? 'text-foreground' : 'text-foreground/90'
                    )}
                    title={title}
                  >
                    {title}
                  </span>
                  <span
                    className={cn(
                      'shrink-0 text-[10px] tabular-nums',
                      isActive ? 'text-muted-foreground' : 'text-muted-foreground/60'
                    )}
                  >
                    {formatRelativeTime(conversation.updated_at)}
                  </span>
                </div>

                <p
                  className={cn(
                    'line-clamp-2 text-xs',
                    isActive ? 'text-muted-foreground' : 'text-muted-foreground/60'
                  )}
                >
                  {conversation.last_message_preview || 'No messages yet'}
                </p>

                {agentLabel && (
                  <div className="flex items-center">
                    <Badge
                      variant="outline"
                      className={cn(
                        'h-5 border-white/10 px-1.5 text-[10px] font-normal uppercase tracking-wider text-muted-foreground',
                        isActive ? 'bg-background/50' : 'bg-white/5'
                      )}
                    >
                      {agentLabel}
                    </Badge>
                  </div>
                )}
              </button>

              {onDeleteConversation && (
                <div
                  className={cn(
                    'absolute right-2 top-2 opacity-0 transition-opacity duration-200 group-hover:opacity-100',
                    isActive && 'opacity-100'
                  )}
                >
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6 rounded-full hover:bg-background/80 hover:text-destructive"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <MoreVertical className="h-3.5 w-3.5" />
                        <span className="sr-only">Options</span>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem
                        className="text-destructive focus:text-destructive"
                        onClick={(e) => {
                          e.stopPropagation();
                          void onDeleteConversation(conversation.id);
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
        })}
      </ul>
    );
  };

  const searchList = renderList(
    searchResults.map((hit) => ({
      id: hit.conversation_id,
      title: hit.topic_hint ?? hit.preview,
      topic_hint: hit.topic_hint,
      agent_entrypoint: hit.agent_entrypoint,
      active_agent: hit.active_agent,
      last_message_preview: hit.last_message_preview ?? hit.preview,
      updated_at: hit.updated_at ?? new Date().toISOString(),
    })),
    isSearching
  );

  return (
    <GlassPanel className={cn('flex h-full w-full flex-col overflow-hidden', className)}>
      {/* Header Section */}
      <div className="flex flex-col gap-4 p-4 pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <History className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold leading-none tracking-tight">History</h2>
              <p className="mt-1 text-[10px] text-muted-foreground">Your conversations</p>
            </div>
          </div>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  onClick={onNewConversation}
                  size="icon"
                  variant="ghost"
                  className="h-8 w-8 rounded-lg hover:bg-primary/10 hover:text-primary"
                >
                  <Plus className="h-5 w-5" />
                  <span className="sr-only">New Chat</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">New Conversation</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>

        {/* Search Input */}
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground/50" />
          <Input
            placeholder="Search transcripts..."
            value={searchTerm}
            onChange={handleSearchChange}
            className="h-9 border-white/10 bg-white/5 pl-9 text-sm focus-visible:ring-primary/20"
          />
        </div>
      </div>

      {/* Tabs & List */}
      <Tabs
        value={tab}
        onValueChange={(value) => setTab(value as 'recent' | 'search')}
        className="flex flex-1 flex-col overflow-hidden"
      >
        <div className="px-4 pb-2">
          <TabsList className="grid w-full grid-cols-2 bg-white/5 p-0.5">
            <TabsTrigger
              value="recent"
              className="h-7 rounded-sm text-xs data-[state=active]:bg-background/50 data-[state=active]:text-foreground data-[state=active]:shadow-sm"
            >
              Recent
            </TabsTrigger>
            <TabsTrigger
              value="search"
              disabled={!searchTerm && tab !== 'search'}
              className="h-7 rounded-sm text-xs data-[state=active]:bg-background/50 data-[state=active]:text-foreground data-[state=active]:shadow-sm"
            >
              Results
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="recent" className="flex-1 overflow-hidden data-[state=inactive]:hidden">
          <ScrollArea className="h-full px-3">
            {renderList(conversationList, isLoadingConversations)}
            {hasNextConversationPage && (
              <div className="flex justify-center py-4">
                <Button variant="ghost" size="sm" onClick={loadMoreConversations} className="h-8 text-xs">
                  Load More
                </Button>
              </div>
            )}
            <div className="h-4" /> {/* Bottom Spacer */}
          </ScrollArea>
        </TabsContent>

        <TabsContent value="search" className="flex-1 overflow-hidden data-[state=inactive]:hidden">
          <ScrollArea className="h-full px-3">
            {showSearchEmpty ? (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <p className="text-sm text-muted-foreground">No matches found.</p>
                <Button
                  variant="link"
                  size="sm"
                  onClick={() => setSearchTerm('')}
                  className="text-xs"
                >
                  Clear search
                </Button>
              </div>
            ) : (
              searchList
            )}
            {hasNextSearchPage && (
              <div className="flex justify-center py-4">
                <Button variant="ghost" size="sm" onClick={loadMoreSearch} className="h-8 text-xs">
                  Load More
                </Button>
              </div>
            )}
            <div className="h-4" /> {/* Bottom Spacer */}
          </ScrollArea>
        </TabsContent>
      </Tabs>
    </GlassPanel>
  );
}
