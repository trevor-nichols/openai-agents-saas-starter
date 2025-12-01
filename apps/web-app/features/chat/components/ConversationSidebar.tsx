// File Path: features/chat/components/ConversationSidebar.tsx
// Description: Glass-styled sidebar for managing conversations.

'use client';

import { useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import { GlassPanel } from '@/components/ui/foundation';
import { EmptyState } from '@/components/ui/states';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';
import { formatRelativeTime } from '@/lib/utils/time';
import type { ConversationListItem } from '@/types/conversations';
import { useConversationSearch } from '@/lib/queries/conversations';
import { InlineTag } from '@/components/ui/foundation';

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

  const {
    results: searchResults,
    isLoading: isSearching,
    loadMore: loadMoreSearch,
    hasNextPage: hasNextSearchPage,
    error: searchError,
  } = useConversationSearch(debounced);

  const showSearchEmpty = !isSearching && !searchResults.length && debounced;
  const renderList = (items: ConversationListItem[], loading: boolean) => {
    if (loading) {
      return (
        <ul className="space-y-3">
          {Array.from({ length: 4 }).map((_, index) => (
            <li key={index} className="animate-pulse rounded-lg border border-white/5 bg-white/5 px-3 py-3">
              <div className="h-4 w-3/4 rounded-full bg-white/15" />
              <div className="mt-2 h-3 w-1/2 rounded-full bg-white/10" />
            </li>
          ))}
        </ul>
      );
    }

    if (!items.length) {
      return (
        <EmptyState
          title="No transcripts yet"
          description="Use the New control to start your first transcript."
        />
      );
    }

    return (
      <ul className="space-y-2">
        {items.map((conversation) => {
          const title =
            conversation.title?.trim() ||
            conversation.topic_hint?.trim() ||
            conversation.last_message_preview?.slice(0, 50) ||
            `Conversation ${conversation.id.substring(0, 8)}…`;

          const agentLabel = conversation.active_agent || conversation.agent_entrypoint;

          return (
            <li key={conversation.id}>
              <button
                type="button"
                onClick={() => onSelectConversation(conversation.id)}
                className={cn(
                  'group flex w-full flex-col gap-1 rounded-lg border px-3 py-2 text-left transition duration-quick ease-apple',
                  currentConversationId === conversation.id
                    ? 'border-primary/50 bg-primary/10 text-foreground'
                    : 'border-white/5 bg-white/5 text-foreground/80 hover:border-white/15 hover:bg-white/10'
                )}
              >
                <div className="flex items-center justify-between gap-2 text-sm font-semibold">
                  <div className="flex items-center gap-2 min-w-0">
                    {agentLabel ? (
                      <InlineTag tone="default" className="shrink-0">
                        {agentLabel}
                      </InlineTag>
                    ) : null}
                    <p className="truncate">{title}</p>
                  </div>
                  <span className="text-xs text-foreground/50" title={conversation.updated_at}>
                    {formatRelativeTime(conversation.updated_at)}
                  </span>
                </div>
                {conversation.last_message_preview ? (
                  <p className="truncate text-xs text-foreground/60">{conversation.last_message_preview}</p>
                ) : null}
              </button>
              {onDeleteConversation ? (
                <div className="mt-1 flex justify-end">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-xs text-foreground/60"
                    onClick={(event) => {
                      event.stopPropagation();
                      void onDeleteConversation(conversation.id);
                    }}
                  >
                    Clear
                  </Button>
                </div>
              ) : null}
            </li>
          );
        })}
      </ul>
    );
  };

  const recentList = renderList(conversationList, isLoadingConversations);
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
    <GlassPanel className={cn('flex h-full w-full flex-col gap-4 p-5', className)}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-foreground/50">Conversations</p>
          <p className="text-sm text-foreground/70">Audit transcripts and jump back in.</p>
        </div>
        <Button size="sm" variant="ghost" className="border border-white/10" onClick={onNewConversation}>
          New
        </Button>
      </div>

      <Tabs value={tab} onValueChange={(value) => setTab(value as 'recent' | 'search')} className="flex flex-1 flex-col">
        <TabsList className="grid grid-cols-2">
          <TabsTrigger value="recent">Recent</TabsTrigger>
          <TabsTrigger value="search">Search</TabsTrigger>
        </TabsList>
        <TabsContent value="recent" className="flex-1">
          <ScrollArea className="flex-1 pr-2">
            {recentList}
            {hasNextConversationPage ? (
              <div className="mt-3 flex justify-center">
                <Button size="sm" variant="ghost" onClick={loadMoreConversations}>
                  Load more
                </Button>
              </div>
            ) : null}
          </ScrollArea>
        </TabsContent>
        <TabsContent value="search" className="flex-1 space-y-3">
          <div className="relative">
            <Input
              placeholder="Search conversations"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <ScrollArea className="flex-1 pr-2">
            {showSearchEmpty ? (
              <EmptyState
                title="No matches"
                description={searchError || 'Try another query.'}
                action={
                  <Button variant="ghost" size="sm" onClick={() => setSearchTerm('')}>
                    Clear
                  </Button>
                }
              />
            ) : (
              searchList
            )}
            {hasNextSearchPage ? (
              <div className="mt-3 flex justify-center">
                <Button size="sm" variant="ghost" onClick={loadMoreSearch}>
                  Load more
                </Button>
              </div>
            ) : null}
          </ScrollArea>
        </TabsContent>
      </Tabs>
    </GlassPanel>
  );
}
