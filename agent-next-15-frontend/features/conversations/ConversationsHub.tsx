'use client';

import { useCallback, useMemo, useState } from 'react';

import Link from 'next/link';
import { Search } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';

import { Button } from '@/components/ui/button';
import { GlassPanel, InlineTag, SectionHeader } from '@/components/ui/foundation';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { useConversations } from '@/lib/queries/conversations';
import { queryKeys } from '@/lib/queries/keys';
import { fetchConversationHistory } from '@/lib/api/conversations';
import { formatRelativeTime } from '@/lib/utils/time';
import { ConversationDetailDrawer } from './ConversationDetailDrawer';

export function ConversationsHub() {
  const {
    conversationList,
    isLoadingConversations,
    error,
    loadConversations,
    removeConversationFromList,
  } = useConversations();

  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const queryClient = useQueryClient();

  const handleSelectConversation = useCallback((conversationId: string) => {
    setSelectedConversationId(conversationId);
  }, []);

  const handleCloseDrawer = useCallback(() => {
    setSelectedConversationId(null);
  }, []);

  const handleConversationDeleted = useCallback(
    (conversationId: string) => {
      removeConversationFromList(conversationId);
      loadConversations();
      setSelectedConversationId(null);
    },
    [loadConversations, removeConversationFromList],
  );

  const totalConversations = conversationList.length;

  const filteredConversations = useMemo(() => {
    if (!searchTerm.trim()) {
      return conversationList;
    }
    const term = searchTerm.toLowerCase();
    return conversationList.filter((conversation) => {
      const title = conversation.title?.toLowerCase() ?? '';
      const summary = conversation.last_message_summary?.toLowerCase() ?? '';
      const id = conversation.id.toLowerCase();
      return title.includes(term) || summary.includes(term) || id.includes(term);
    });
  }, [conversationList, searchTerm]);

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

  const visibleCount = filteredConversations.length;
  const isSearching = Boolean(searchTerm.trim());

  return (
    <section className="space-y-8">
      <SectionHeader
        eyebrow="Audit"
        title="Conversation archive"
        description="Search, filter, and export transcripts for compliance-ready reviews."
        actions={
          <div className="flex items-center gap-3">
            <InlineTag tone={totalConversations ? 'positive' : 'default'}>
              {isLoadingConversations
                ? 'Loading…'
                : isSearching
                  ? `${visibleCount}/${totalConversations} matches`
                  : `${totalConversations} threads`}
            </InlineTag>
            <Button variant="ghost" size="sm" onClick={loadConversations} disabled={isLoadingConversations}>
              Refresh
            </Button>
            <Button asChild size="sm">
              <Link href="/chat">Open workspace</Link>
            </Button>
          </div>
        }
      />

      <GlassPanel>
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-sm font-semibold text-foreground">Conversations</p>
              <p className="text-xs text-foreground/60">Chronological list of all transcripts.</p>
            </div>
            <div className="flex w-full gap-3 lg:w-auto">
              <div className="relative flex-1">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/50" />
                <Input
                  value={searchTerm}
                  onChange={(event) => setSearchTerm(event.target.value)}
                  placeholder="Search by title, summary, or ID"
                  className="pl-9"
                />
              </div>
              {isSearching ? (
                <Button variant="secondary" onClick={() => setSearchTerm('')}>
                  Clear
                </Button>
              ) : null}
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/5">
            {isLoadingConversations ? (
              <SkeletonPanel lines={8} className="rounded-2xl border-0 bg-transparent" />
            ) : error ? (
              <ErrorState message={error} onRetry={loadConversations} />
            ) : totalConversations === 0 ? (
              <EmptyState
                title="No conversations yet"
                description="Launch a chat to generate your first transcript."
                action={<Button asChild><Link href="/chat">Start chatting</Link></Button>}
              />
            ) : visibleCount === 0 ? (
              <EmptyState
                title="No results found"
                description="Try a different search term or clear the filter to see all transcripts."
                action={
                  <Button variant="ghost" onClick={() => setSearchTerm('')}>
                    Clear search
                  </Button>
                }
              />
            ) : (
              <ScrollArea className="max-h-[480px]">
                <table className="w-full text-sm text-foreground/80">
                  <thead className="sticky top-0 bg-white/10 text-left text-xs uppercase tracking-[0.2em] text-foreground/50">
                    <tr>
                      <th className="px-4 py-3">Title</th>
                      <th className="px-4 py-3">Summary</th>
                      <th className="px-4 py-3">Last activity</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredConversations.map((conversation) => (
                      <tr
                        key={conversation.id}
                        className="cursor-pointer border-t border-white/5 transition hover:bg-white/5 focus-visible:bg-white/10"
                        onClick={() => handleSelectConversation(conversation.id)}
                        onMouseEnter={() => handlePrefetch(conversation.id)}
                        onFocus={() => handlePrefetch(conversation.id)}
                        tabIndex={0}
                        onKeyDown={(event) => {
                          if (event.key === 'Enter' || event.key === ' ') {
                            event.preventDefault();
                            handleSelectConversation(conversation.id);
                          }
                        }}
                        aria-label={`Open conversation ${conversation.title ?? conversation.id}`}
                      >
                        <td className="px-4 py-3 font-semibold text-foreground">
                          {conversation.title ?? `Conversation ${conversation.id.substring(0, 8)}…`}
                        </td>
                        <td className="px-4 py-3 text-foreground/70">
                          {conversation.last_message_summary ?? 'Awaiting summary'}
                        </td>
                        <td className="px-4 py-3 text-foreground/60">{formatRelativeTime(conversation.updated_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </ScrollArea>
            )}
          </div>
        </div>
      </GlassPanel>

      <ConversationDetailDrawer
        conversationId={selectedConversationId}
        open={Boolean(selectedConversationId)}
        onClose={handleCloseDrawer}
        onDeleted={handleConversationDeleted}
      />
    </section>
  );
}
