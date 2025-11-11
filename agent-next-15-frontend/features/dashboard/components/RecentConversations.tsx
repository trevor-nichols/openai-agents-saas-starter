import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { GlassPanel, SectionHeader } from '@/components/ui/foundation';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import { formatRelativeTime } from '@/lib/utils/time';

import type { RecentConversationSummary } from '../types';

interface RecentConversationsProps {
  conversations: RecentConversationSummary[];
  isLoading: boolean;
  error?: string | null;
  onRefresh?: () => void;
}

export function RecentConversations({ conversations, isLoading, error, onRefresh }: RecentConversationsProps) {
  if (isLoading) {
    return <SkeletonPanel lines={6} />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={onRefresh} />;
  }

  if (!conversations.length) {
    return (
      <EmptyState
        title="No recent conversations"
        description="Once messages start flowing, they will show up here for quick inspection."
        action={
          <Button asChild>
            <Link href="/chat">Open chat workspace</Link>
          </Button>
        }
      />
    );
  }

  return (
    <GlassPanel className="space-y-6">
      <SectionHeader
        eyebrow="Activity"
        title="Recent conversations"
        description="Audit summaries from the last few sessions."
        actions={
          onRefresh ? (
            <Button variant="ghost" size="sm" onClick={onRefresh}>
              Refresh
            </Button>
          ) : null
        }
      />

      <div className="space-y-3">
        {conversations.map((conversation) => (
          <div key={conversation.id} className="rounded-lg border border-white/5 bg-white/5 px-4 py-3">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm font-semibold text-foreground">{conversation.title}</p>
                <p className="text-xs text-foreground/60">{conversation.summary}</p>
              </div>
              <p className="text-xs text-foreground/50">{formatRelativeTime(conversation.updatedAt)}</p>
            </div>
          </div>
        ))}
      </div>
    </GlassPanel>
  );
}
