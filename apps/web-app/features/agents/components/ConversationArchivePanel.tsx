// File Path: features/agents/components/ConversationArchivePanel.tsx
// Description: Auditable table of past conversations with search + prefetch.

'use client';

import { useCallback, useMemo, useState, useEffect } from 'react';
import Link from 'next/link';
import type { ColumnDef } from '@tanstack/react-table';
import { useQueryClient } from '@tanstack/react-query';
import { Search } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { DataTable } from '@/components/ui/data-table';
import { GlassPanel, InlineTag, SectionHeader } from '@/components/ui/foundation';
import { EmptyState } from '@/components/ui/states';
import { Input } from '@/components/ui/input';
import { fetchConversationHistory } from '@/lib/api/conversations';
import { useConversationSearch } from '@/lib/queries/conversations';
import { queryKeys } from '@/lib/queries/keys';
import { formatRelativeTime } from '@/lib/utils/time';
import type { ConversationListItem } from '@/types/conversations';

interface ConversationArchivePanelProps {
  conversationList: ConversationListItem[];
  isLoading: boolean;
  error: string | null;
  onRefresh: () => void;
   onLoadMore?: () => void;
  hasNextPage?: boolean;
  onSelectConversation: (conversationId: string) => void;
}

export function ConversationArchivePanel({
  conversationList,
  isLoading,
  error,
  onRefresh,
  onLoadMore,
  hasNextPage,
  onSelectConversation,
}: ConversationArchivePanelProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [debounced, setDebounced] = useState('');
  const queryClient = useQueryClient();

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

  const filteredConversations = useMemo(() => {
    if (debounced) {
      return searchResults.map((hit) => ({
        id: hit.conversation_id,
        title: hit.topic_hint ?? hit.preview,
        topic_hint: hit.topic_hint,
        last_message_preview: hit.last_message_preview ?? hit.preview,
        updated_at: hit.updated_at ?? new Date().toISOString(),
      }));
    }
    return conversationList;
  }, [conversationList, debounced, searchResults]);

  const totalCount = conversationList.length;
  const visibleCount = filteredConversations.length;
  const isSearchingActive = Boolean(debounced);

  const columns = useMemo<ConversationColumn[]>(() => {
    return [
      {
        id: 'title',
        header: 'Title',
        cell: ({ row }) => (
          <div className="font-semibold text-foreground">
            {row.original.topic_hint ?? row.original.title ?? `Conversation ${row.original.id.substring(0, 8)}…`}
          </div>
        ),
      },
      {
        id: 'summary',
        header: 'Summary',
        cell: ({ row }) => (
          <span className="text-foreground/70">
            {row.original.last_message_preview ?? 'Awaiting summary'}
          </span>
        ),
      },
      {
        id: 'updated',
        header: 'Last activity',
        cell: ({ row }) => (
          <span className="text-foreground/60">{formatRelativeTime(row.original.updated_at)}</span>
        ),
      },
    ];
  }, []);

  const handlePrefetch = useCallback(
    (conversationId: string) => {
      queryClient.prefetchQuery({
        queryKey: queryKeys.conversations.detail(conversationId),
        queryFn: () => fetchConversationHistory(conversationId),
        staleTime: 5 * 60 * 1000,
      });
    },
    [queryClient],
  );

  const tableEmptyState = isSearchingActive ? (
    <EmptyState
      title="No results found"
      description={searchError || 'Try a different search term or clear the filter to see all transcripts.'}
      action={
        <Button variant="ghost" onClick={() => setSearchTerm('')}>
          Clear search
        </Button>
      }
    />
  ) : (
    <EmptyState
      title="No conversations yet"
      description="Launch a chat to generate your first transcript."
      action={
        <Button asChild>
          <Link href="/chat">Start chatting</Link>
        </Button>
      }
    />
  );

  return (
    <GlassPanel className="space-y-6">
      <SectionHeader
        eyebrow="Audit"
        title="Conversation archive"
        description="Search, filter, and export transcripts for compliance-ready reviews."
        actions={
        <div className="flex items-center gap-3">
          <InlineTag tone={totalCount ? 'positive' : 'default'}>
            {isLoading
              ? 'Loading…'
              : isSearchingActive
                ? `${visibleCount}/${totalCount} matches`
                : `${totalCount} threads`}
          </InlineTag>
          <Button variant="ghost" size="sm" onClick={onRefresh} disabled={isLoading}>
            Refresh
            </Button>
          </div>
        }
      />

      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="w-full md:max-w-sm">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/50" />
            <Input
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search by title, summary, or ID"
              className="pl-9"
            />
          </div>
        </div>
        {isSearchingActive ? (
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setSearchTerm('')}
            disabled={isSearching}
          >
            Clear filter
          </Button>
        ) : null}
      </div>

      <DataTable
        columns={columns}
        data={filteredConversations}
        className="rounded-2xl border border-white/10 bg-white/5"
        isLoading={isLoading}
        isError={Boolean(error)}
        error={error ?? undefined}
        emptyState={tableEmptyState}
        onRowClick={(row) => onSelectConversation(row.original.id)}
        onRowMouseEnter={(row) => handlePrefetch(row.original.id)}
        onRowFocus={(row) => handlePrefetch(row.original.id)}
        enableSorting={false}
        enablePagination={false}
      />

      {!debounced && hasNextPage ? (
        <div className="flex justify-center">
          <Button variant="ghost" size="sm" onClick={onLoadMore} disabled={isLoading}>
            Load more
          </Button>
        </div>
      ) : null}

      {debounced && hasNextSearchPage ? (
        <div className="flex justify-center">
          <Button variant="ghost" size="sm" onClick={loadMoreSearch} disabled={isSearching}>
            Load more results
          </Button>
        </div>
      ) : null}
    </GlassPanel>
  );
}

type ConversationColumn = ColumnDef<ConversationListItem, unknown>;
