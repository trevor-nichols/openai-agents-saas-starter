'use client';

import Link from 'next/link';
import { BellIcon } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import { formatRelativeTime } from '@/lib/utils/time';
import { useRecentActivity } from '@/lib/queries/activity';

const MAX_ITEMS = 8;

export function AppNotificationMenu() {
  const {
    items,
    badgeCount,
    streamStatus,
    isLoading,
    error,
    refresh,
  } = useRecentActivity({ limit: MAX_ITEMS, live: true });

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="h-9 w-9 relative">
          <BellIcon className="h-4 w-4" />
          {badgeCount > 0 && (
            <Badge className="absolute -top-1 -right-1 h-5 min-w-[1.25rem] w-auto px-1.5 flex items-center justify-center text-[10px] font-semibold">
              {badgeCount > 9 ? '9+' : badgeCount}
            </Badge>
          )}
          <span className="sr-only">Notifications</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-96">
        <DropdownMenuLabel className="flex items-center justify-between text-sm font-medium">
          <span>Activity</span>
          <StreamStatusPill status={streamStatus} />
        </DropdownMenuLabel>
        <DropdownMenuSeparator />

        {isLoading ? (
          <NotificationSkeleton />
        ) : error ? (
          <div className="px-3 py-2 space-y-2 text-sm">
            <p className="text-foreground">Unable to load notifications.</p>
            <Button variant="ghost" size="sm" onClick={refresh}>
              Retry
            </Button>
          </div>
        ) : items.length === 0 ? (
          <div className="px-3 py-2 text-sm text-muted-foreground">No recent activity yet.</div>
        ) : (
          <ScrollArea className="max-h-[420px] pr-2">
            <div className="py-1">
              {items.map((item, idx) => (
                <div key={item.id}>
                  <DropdownMenuItem asChild className="cursor-default focus:bg-accent">
                    <div className="flex w-full gap-3 py-2">
                      <Badge variant={badgeVariant(item.status)} className="mt-0.5 h-5 px-1.5 text-[10px] capitalize">
                        {item.status}
                      </Badge>
                      <div className="flex min-w-0 flex-col gap-1">
                        <div className="flex items-start justify-between gap-2">
                          <p className="text-sm font-medium text-foreground truncate">{item.title}</p>
                          <span className="text-xs text-muted-foreground whitespace-nowrap">
                            {formatRelativeTime(item.timestamp)}
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground truncate">{item.detail}</p>
                        {item.metadataSummary ? (
                          <p className="text-[11px] text-muted-foreground/70 line-clamp-1">{item.metadataSummary}</p>
                        ) : null}
                      </div>
                    </div>
                  </DropdownMenuItem>
                  {idx < items.length - 1 && <Separator className="my-1" />}
                </div>
              ))}
            </div>
          </ScrollArea>
        )}

        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link href="/dashboard" className="flex w-full items-center justify-between text-sm">
            View dashboard activity
            <span className="text-xs text-muted-foreground">Open</span>
          </Link>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function badgeVariant(status: 'success' | 'failure' | 'pending') {
  switch (status) {
    case 'success':
      return 'secondary' as const;
    case 'pending':
      return 'outline' as const;
    case 'failure':
    default:
      return 'destructive' as const;
  }
}

function StreamStatusPill({ status }: { status: 'idle' | 'connecting' | 'open' | 'closed' | 'error' }) {
  const label =
    status === 'open'
      ? 'Live'
      : status === 'connecting'
        ? 'Connecting'
        : status === 'error'
          ? 'Error'
          : status === 'idle'
            ? 'Idle'
            : 'Paused';

  const tone =
    status === 'open'
      ? 'bg-emerald-500/80'
      : status === 'error'
        ? 'bg-destructive/80'
        : 'bg-muted';

  return (
    <span className={cn('inline-flex items-center gap-1 rounded-full px-2 py-1 text-[11px] capitalize', tone)}>
      <span className={cn('h-2 w-2 rounded-full', tone)} />
      {label}
    </span>
  );
}

function NotificationSkeleton() {
  return (
    <div className="space-y-3 px-3 py-2">
      {Array.from({ length: 4 }).map((_, idx) => (
        <div key={idx} className="flex items-start gap-3">
          <Skeleton className="h-5 w-12" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
            <Skeleton className="h-3 w-2/3" />
          </div>
        </div>
      ))}
    </div>
  );
}
