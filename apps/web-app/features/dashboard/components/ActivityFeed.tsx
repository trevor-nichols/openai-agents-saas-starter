import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { GlassPanel, SectionHeader } from '@/components/ui/foundation';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import { formatRelativeTime } from '@/lib/utils/time';

import type { ActivityFeedItem } from '../types';
import { DASHBOARD_COPY } from '../constants';

interface ActivityFeedProps {
  items: ActivityFeedItem[];
  isLoading: boolean;
  error?: string | null;
  onRefresh?: () => void;
}

export function ActivityFeed({ items, isLoading, error, onRefresh }: ActivityFeedProps) {
  if (isLoading) {
    return <SkeletonPanel lines={6} />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={onRefresh} />;
  }

  if (!items.length) {
    return (
      <EmptyState
        title={DASHBOARD_COPY.activityFeed.emptyTitle}
        description={DASHBOARD_COPY.activityFeed.emptyDescription}
        action={
          onRefresh ? (
            <Button variant="ghost" size="sm" onClick={onRefresh}>
              Refresh
            </Button>
          ) : null
        }
      />
    );
  }

  return (
    <GlassPanel className="space-y-6">
      <SectionHeader
        eyebrow="Activity"
        title={DASHBOARD_COPY.activityFeed.title}
        description={DASHBOARD_COPY.activityFeed.description}
        actions={
          onRefresh ? (
            <Button variant="ghost" size="sm" onClick={onRefresh}>
              Refresh
            </Button>
          ) : null
        }
      />

      <div className="space-y-3">
        {items.map((event) => (
          <div
            key={event.id}
            className="rounded-lg border border-white/5 bg-white/5 px-4 py-3"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-semibold text-foreground">{event.title}</p>
                  <Badge variant={badgeVariant(event.status)} className="text-[11px]">
                    {event.status}
                  </Badge>
                </div>
                <p className="text-xs text-foreground/70">{event.detail}</p>
                {event.metadataSummary ? (
                  <p className="text-[11px] text-foreground/50">{event.metadataSummary}</p>
                ) : null}
              </div>
              <p className="text-xs text-foreground/50 whitespace-nowrap">
                {formatRelativeTime(event.timestamp)}
              </p>
            </div>
          </div>
        ))}
      </div>
    </GlassPanel>
  );
}

function badgeVariant(
  status: ActivityFeedItem['status'],
): 'secondary' | 'outline' | 'destructive' {
  switch (status) {
    case 'success':
      return 'secondary';
    case 'pending':
      return 'outline';
    case 'failure':
    default:
      return 'destructive';
  }
}
