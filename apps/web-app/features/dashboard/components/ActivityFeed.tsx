import { Activity } from 'lucide-react';

import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { GlassPanel, SectionHeader } from '@/components/ui/foundation';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
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
    <GlassPanel className="flex h-full flex-col space-y-6">
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

      <ScrollArea className="h-[400px] pr-4">
        <div className="flex flex-col gap-4">
          {items.map((event, index) => (
            <div key={event.id}>
              <div className="flex gap-4">
                <Avatar className="h-9 w-9 border border-white/10">
                  <AvatarFallback className="bg-white/5 text-xs text-muted-foreground">
                    <Activity className="h-4 w-4" />
                  </AvatarFallback>
                </Avatar>
                
                <div className="flex min-w-0 flex-1 flex-col gap-1">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-medium leading-none text-foreground">
                      {event.title}
                    </p>
                    <span className="text-xs text-muted-foreground whitespace-nowrap">
                      {formatRelativeTime(event.timestamp)}
                    </span>
                  </div>
                  
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span className="truncate">{event.detail}</span>
                    {event.status !== 'success' && (
                      <Badge variant={badgeVariant(event.status)} className="h-5 px-1.5 text-[10px]">
                        {event.status}
                      </Badge>
                    )}
                  </div>

                  {event.metadataSummary ? (
                    <p className="line-clamp-1 text-[11px] text-muted-foreground/60">
                      {event.metadataSummary}
                    </p>
                  ) : null}
                </div>
              </div>
              {index < items.length - 1 && <Separator className="mt-4 bg-white/5" />}
            </div>
          ))}
        </div>
      </ScrollArea>
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
