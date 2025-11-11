'use client';

import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { GlassPanel, InlineTag, SectionHeader } from '@/components/ui/foundation';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useConversations } from '@/lib/queries/conversations';
import { formatRelativeTime } from '@/lib/utils/time';

export function ConversationsHub() {
  const {
    conversationList,
    isLoadingConversations,
    error,
    loadConversations,
  } = useConversations();

  const totalConversations = conversationList.length;

  return (
    <section className="space-y-8">
      <SectionHeader
        eyebrow="Audit"
        title="Conversation archive"
        description="Search, filter, and export transcripts for compliance-ready reviews."
        actions={
          <div className="flex items-center gap-3">
            <InlineTag tone={totalConversations ? 'positive' : 'default'}>
              {isLoadingConversations ? 'Loading…' : `${totalConversations} threads`}
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
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-semibold text-foreground">Conversations</p>
              <p className="text-xs text-foreground/60">Chronological list of all transcripts.</p>
            </div>
            <Button variant="ghost" size="sm" className="border border-white/10" disabled>
              Filters coming soon
            </Button>
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
                    {conversationList.map((conversation) => (
                      <tr key={conversation.id} className="border-t border-white/5">
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
    </section>
  );
}
