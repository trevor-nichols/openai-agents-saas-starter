'use client';

import Link from 'next/link';
import { BellIcon, CheckIcon, XIcon, ActivityIcon } from 'lucide-react';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import { formatRelativeTime } from '@/lib/utils/time';
import { useRecentActivity } from '@/lib/queries/activity';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { dismissActivity, markActivityRead, markAllActivityRead } from '@/lib/api/activity';
import { queryKeys } from '@/lib/queries/keys';
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from '@/components/ui/tooltip';

const MAX_ITEMS = 8;

export function AppNotificationMenu() {
  const [showDismissed, setShowDismissed] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  const {
    items,
    badgeCount,
    isLoading,
    error,
    refresh,
  } = useRecentActivity({ limit: MAX_ITEMS, live: true, includeDismissed: showDismissed });
  const queryClient = useQueryClient();

  // Optimistic updates could be added here for even snappier feel, currently relying on invalidation
  const invalidateActivity = () =>
    queryClient.invalidateQueries({ queryKey: queryKeys.activity.list({ limit: MAX_ITEMS * 2 }) });

  const markReadMutation = useMutation({
    mutationFn: markActivityRead,
    onSettled: invalidateActivity,
  });

  const dismissMutation = useMutation({
    mutationFn: dismissActivity,
    onSettled: invalidateActivity,
  });

  const markAllMutation = useMutation({
    mutationFn: markAllActivityRead,
    onSettled: invalidateActivity,
  });

  const hasUnread = items.some(i => i.readState === 'unread');

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <TooltipProvider delayDuration={300}>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" className="group relative h-9 w-9 data-[state=open]:bg-muted">
            <BellIcon className="h-4 w-4 transition-transform group-hover:scale-110 text-muted-foreground group-hover:text-foreground" />
            <AnimatePresence>
              {badgeCount > 0 && (
                <motion.span
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  exit={{ scale: 0 }}
                  className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white shadow-sm ring-2 ring-background pointer-events-none"
                >
                  {badgeCount > 9 ? '9+' : badgeCount}
                </motion.span>
              )}
            </AnimatePresence>
            <span className="sr-only">Notifications</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-[420px] p-0 overflow-hidden rounded-xl border-border shadow-2xl bg-popover/95 backdrop-blur-sm">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b bg-muted/30">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold tracking-tight">Activity</span>
            </div>
            <div className="flex items-center gap-2">
              {hasUnread && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6 text-muted-foreground hover:text-foreground"
                      onClick={() => markAllMutation.mutate()}
                      disabled={markAllMutation.isPending}
                    >
                      <CheckIcon className="h-3.5 w-3.5" />
                      <span className="sr-only">Mark all read</span>
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Mark all read</TooltipContent>
                </Tooltip>
              )}
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-foreground" asChild>
                    <Link href="/dashboard">
                      <ActivityIcon className="h-3.5 w-3.5" />
                      <span className="sr-only">View Dashboard</span>
                    </Link>
                  </Button>
                </TooltipTrigger>
                <TooltipContent>View Full Dashboard</TooltipContent>
              </Tooltip>
            </div>
          </div>

          {/* Content */}
          <ScrollArea className="h-[400px]">
            <div className="p-0">
              {isLoading ? (
                <NotificationSkeleton />
              ) : error ? (
                <ErrorState refresh={refresh} />
              ) : items.length === 0 ? (
                <EmptyState />
              ) : (
                <ul className="divide-y divide-border/50">
                  <AnimatePresence initial={false}>
                    {items.map((item) => (
                      <NotificationItem
                        key={item.id}
                        item={item}
                        onMarkRead={markReadMutation.mutate}
                        onDismiss={dismissMutation.mutate}
                      />
                    ))}
                  </AnimatePresence>
                </ul>
              )}
            </div>
          </ScrollArea>

          {/* Footer */}
          <div className="flex items-center justify-between px-4 py-2 border-t bg-muted/30 text-xs text-muted-foreground">
            <div className="flex items-center gap-2">
              <Switch
                id="show-dismissed"
                checked={showDismissed}
                onCheckedChange={setShowDismissed}
                className="scale-75 origin-left"
              />
              <label htmlFor="show-dismissed" className="cursor-pointer select-none font-medium hover:text-primary transition-colors">
                Show dismissed
              </label>
            </div>
            <div className="flex gap-2 text-[10px] opacity-70">
              <span>{items.length} items</span>
            </div>
          </div>
        </DropdownMenuContent>
      </TooltipProvider>
    </DropdownMenu>
  );
}

// ------------------------------------------------------------------
// Sub-components
// ------------------------------------------------------------------

function NotificationItem({
  item,
  onMarkRead,
  onDismiss,
}: {
  item: any;
  onMarkRead: (id: string) => void;
  onDismiss: (id: string) => void;
}) {
  const isUnread = item.readState === 'unread';
  const isDismissed = item.readState === 'dismissed';

  return (
    <motion.li
      layout
      initial={{ opacity: 0, y: 5 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, height: 0, transition: { duration: 0.2 } }}
      className={cn(
        "group flex gap-3 p-4 transition-colors hover:bg-muted/50",
        isUnread ? "bg-primary/5" : "bg-background"
      )}
    >
      {/* Status Indicator Line */}
      <div className={cn(
        "absolute left-0 top-0 bottom-0 w-[3px]",
        item.status === 'failure' ? "bg-red-500" :
          item.status === 'success' ? "bg-emerald-500" : "bg-transparent"
      )} />

      {/* Icon / Avatar substitute */}
      <div className="pt-1">
        <div className={cn(
          "h-8 w-8 rounded-full flex items-center justify-center border",
          item.status === 'failure' ? 'border-red-200 bg-red-50 text-red-600 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-400' :
            item.status === 'success' ? 'border-emerald-200 bg-emerald-50 text-emerald-600 dark:border-emerald-900/50 dark:bg-emerald-950/30 dark:text-emerald-400' :
              'border-slate-200 bg-slate-50 text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400'
        )}>
          {item.status === 'failure' ? <XIcon className="w-4 h-4" /> :
            item.status === 'success' ? <CheckIcon className="w-4 h-4" /> :
              <ActivityIcon className="w-4 h-4" />}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 space-y-1">
        <div className="flex items-start justify-between gap-2 h-5">
          <h4 className={cn("text-sm font-medium leading-none truncate", isUnread ? "text-foreground" : "text-muted-foreground")}>
            {item.title}
          </h4>

          {/* Timestamp / Actions Swap */}
          <div className="relative flex items-center justify-end min-w-[60px]">
            {/* Timestamp - Fades out on hover */}
            <span className="text-[10px] text-muted-foreground whitespace-nowrap tabular-nums transition-opacity duration-200 group-hover:opacity-0 absolute right-0">
              {formatRelativeTime(item.timestamp)}
            </span>

            {/* Actions - Fades in on hover */}
            <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 absolute right-0">
              {!isDismissed && isUnread && (
                <button
                  className="text-muted-foreground hover:text-emerald-500 transition-colors"
                  onClick={(e) => { e.stopPropagation(); onMarkRead(item.id); }}
                  aria-label="Mark read"
                >
                  <CheckIcon className="h-4 w-4" />
                </button>
              )}
              {!isDismissed && (
                <button
                  className="text-muted-foreground hover:text-red-500 transition-colors"
                  onClick={(e) => { e.stopPropagation(); onDismiss(item.id); }}
                  aria-label="Dismiss"
                >
                  <XIcon className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>
        </div>

        <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
          {item.detail}
        </p>

        {item.metadataSummary && (
          <div className="text-[10px] items-center gap-1.5 inline-flex bg-muted/50 px-1.5 py-0.5 rounded text-muted-foreground/80 mt-1.5 font-mono">
            {item.metadataSummary}
          </div>
        )}
      </div>

      {isDismissed && (
        <Badge variant="secondary" className="absolute right-2 top-2 text-[10px] bg-muted text-muted-foreground pointer-events-none">
          Dismissed
        </Badge>
      )}
    </motion.li>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center space-y-3">
      <div className="h-10 w-10 bg-muted rounded-full flex items-center justify-center">
        <BellIcon className="h-5 w-5 text-muted-foreground/50" />
      </div>
      <p className="text-sm font-medium text-foreground">All caught up!</p>
      <p className="text-xs text-muted-foreground max-w-[180px]">
        No recent activity to show right now.
      </p>
    </div>
  );
}

function ErrorState({ refresh }: { refresh: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-8 px-4 text-center space-y-3 transition-colors hover:bg-muted/50">
      <p className="text-sm text-destructive font-medium">Unable to load notifications</p>
      <Button variant="outline" size="sm" onClick={refresh} className="h-7 text-xs">
        Try Again
      </Button>
    </div>
  );
}

function NotificationSkeleton() {
  return (
    <div className="space-y-4 p-4">
      {Array.from({ length: 3 }).map((_, idx) => (
        <div key={idx} className="flex gap-4">
          <Skeleton className="h-8 w-8 rounded-full flex-shrink-0" />
          <div className="space-y-2 flex-1">
            <Skeleton className="h-3 w-3/4" />
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-2 w-1/4" />
          </div>
        </div>
      ))}
    </div>
  );
}

