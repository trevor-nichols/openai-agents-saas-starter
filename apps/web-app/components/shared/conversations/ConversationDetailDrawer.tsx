// File Path: components/shared/conversations/ConversationDetailDrawer.tsx
// Description: Shared slide-over drawer that surfaces full transcript metadata for a selected conversation.

'use client';

import { useCallback, useMemo, useState } from 'react';

import { Clipboard, Download, Loader2 } from 'lucide-react';

import { deleteConversationById } from '@/lib/api/conversations';
import { useConversationDetail } from '@/lib/queries/conversations';
import { formatRelativeTime } from '@/lib/utils/time';
import { useToast } from '@/components/ui/use-toast';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { InlineTag, GlassPanel, KeyValueList } from '@/components/ui/foundation';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';

interface ConversationDetailDrawerProps {
  conversationId: string | null;
  open: boolean;
  onClose: () => void;
  /**
   * Optional hook that allows parent features to keep list state in sync once a transcript is deleted.
   */
  onDeleted?: (conversationId: string) => void;
  /**
   * Override deletion logic (e.g., use controller-aware mutation inside chat workspace).
   */
  onDeleteConversation?: (conversationId: string) => Promise<void>;
}

export function ConversationDetailDrawer({
  conversationId,
  open,
  onClose,
  onDeleted,
  onDeleteConversation,
}: ConversationDetailDrawerProps) {
  const {
    conversationHistory,
    isLoadingDetail,
    isFetchingDetail,
    detailError,
    refetchDetail,
  } = useConversationDetail(open ? conversationId : null);
  const messages = conversationHistory?.messages ?? [];
  const { success, error, info } = useToast();
  const [isDeleting, setIsDeleting] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const metadataItems = useMemo(() => {
    if (!conversationHistory) {
      return [];
    }
    const messageCount = messages.length;
    return [
      { label: 'Conversation ID', value: conversationHistory.conversation_id },
      { label: 'Created', value: formatAbsolute(conversationHistory.created_at) },
      { label: 'Updated', value: formatAbsolute(conversationHistory.updated_at) },
      { label: 'Messages', value: messageCount.toString() },
    ];
  }, [conversationHistory, messages.length]);

  const agentContextItems = useMemo(() => {
    if (!conversationHistory?.agent_context) {
      return [];
    }
    return Object.entries(conversationHistory.agent_context).map(([key, value]) => ({
      label: key,
      value: typeof value === 'string' ? (
        value
      ) : (
        <code className="block whitespace-pre-wrap break-words text-xs font-mono text-foreground/80">
          {JSON.stringify(value, null, 2)}
        </code>
      ),
    }));
  }, [conversationHistory?.agent_context]);

  const handleDelete = useCallback(async () => {
    if (!conversationId) {
      return;
    }
    setIsDeleting(true);
    try {
      const deleteFn = onDeleteConversation ?? deleteConversationById;
      await deleteFn(conversationId);
      success({
        title: 'Conversation deleted',
        description: 'The transcript has been removed from the archive.',
      });
      onDeleted?.(conversationId);
      onClose();
    } catch (err) {
      error({
        title: 'Failed to delete conversation',
        description: err instanceof Error ? err.message : 'Unknown error occurred.',
      });
    } finally {
      setIsDeleting(false);
    }
  }, [conversationId, error, onClose, onDeleteConversation, onDeleted, success]);

  const handleExport = useCallback(async () => {
    if (!conversationHistory) {
      return;
    }
    setIsExporting(true);
    try {
      const blob = new Blob([JSON.stringify(conversationHistory, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${conversationHistory.conversation_id}.json`;
      link.click();
      URL.revokeObjectURL(url);
      info({
        title: 'Export ready',
        description: 'Downloaded JSON transcript. CSV/PDF coming soon.',
      });
    } catch (err) {
      error({
        title: 'Failed to export',
        description: err instanceof Error ? err.message : 'Try again shortly.',
      });
    } finally {
      setIsExporting(false);
    }
  }, [conversationHistory, error, info]);

  const handleRetry = useCallback(() => {
    void refetchDetail();
  }, [refetchDetail]);

  const handleCopyConversationId = useCallback(async () => {
    if (!conversationHistory) return;
    try {
      await navigator.clipboard.writeText(conversationHistory.conversation_id);
      success({ title: 'Copied conversation ID' });
    } catch (err) {
      error({ title: 'Unable to copy ID', description: err instanceof Error ? err.message : undefined });
    }
  }, [conversationHistory, error, success]);

  const handleCopyMessage = useCallback(
    async (content: string) => {
      try {
        await navigator.clipboard.writeText(content);
        success({ title: 'Message copied' });
      } catch (err) {
        error({ title: 'Unable to copy message', description: err instanceof Error ? err.message : undefined });
      }
    },
    [error, success],
  );

  return (
    <Sheet open={open} onOpenChange={(nextOpen) => (!nextOpen ? onClose() : undefined)}>
      <SheetContent side="right" className="w-full overflow-y-auto sm:max-w-xl">
        <SheetHeader>
          <div className="flex items-center gap-2">
            <SheetTitle>Conversation detail</SheetTitle>
            {isFetchingDetail ? (
              <Badge variant="outline" className="gap-2 text-xs text-foreground/70">
                <Loader2 className="h-3.5 w-3.5 animate-spin" /> Refreshing
              </Badge>
            ) : null}
          </div>
          <SheetDescription>
            Review the full transcript, metadata, and lifecycle actions for this conversation.
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {isLoadingDetail ? (
            <SkeletonPanel lines={8} />
          ) : detailError ? (
            <ErrorState message={detailError} onRetry={handleRetry} />
          ) : conversationHistory ? (
            <>
              <GlassPanel className="space-y-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm font-semibold text-foreground">Transcript metadata</p>
                  <p className="text-xs text-foreground/60">
                    Updated {formatRelativeTime(conversationHistory.updated_at)}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <InlineTag tone="default">{messages.length} messages</InlineTag>
                  <Button size="sm" variant="outline" onClick={handleCopyConversationId}>
                    Copy ID
                  </Button>
                    <Button size="sm" variant="outline" onClick={handleExport} disabled={isExporting}>
                      {isExporting ? (
                        <span className="flex items-center gap-2">
                          <Loader2 className="h-3 w-3 animate-spin" /> Preparing
                        </span>
                      ) : (
                        <span className="flex items-center gap-2">
                          <Download className="h-3 w-3" /> Export JSON
                        </span>
                      )}
                    </Button>
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button size="sm" variant="destructive" disabled={isDeleting}>
                          Delete
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Delete this conversation?</AlertDialogTitle>
                          <AlertDialogDescription>
                            This permanently removes the transcript and cannot be undone.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
                          <AlertDialogAction onClick={handleDelete} disabled={isDeleting}>
                            {isDeleting ? 'Deleting…' : 'Delete transcript'}
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </div>
                </div>
                <KeyValueList items={metadataItems} columns={2} />
              </GlassPanel>

              {agentContextItems.length ? (
                <GlassPanel className="space-y-4">
                  <div>
                    <p className="text-sm font-semibold text-foreground">Agent context</p>
                    <p className="text-xs text-foreground/60">Captured at the time of the run.</p>
                  </div>
                  <KeyValueList items={agentContextItems} />
                </GlassPanel>
              ) : null}

              <GlassPanel className="space-y-4">
                <div>
                  <p className="text-sm font-semibold text-foreground">Message timeline</p>
                  <p className="text-xs text-foreground/60">Full transcript in chronological order.</p>
                </div>
                <ScrollArea className="max-h-[480px] pr-4">
                  <div className="space-y-4">
                    {messages.map((message, index) => (
                      <div
                        key={`${message.role}-${index}-${message.timestamp ?? index}`}
                        className="space-y-2 rounded-xl border border-white/5 bg-white/5 p-4"
                      >
                        <div className="flex flex-wrap items-center justify-between gap-3">
                          <div className="flex items-center gap-2">
                            <Badge variant="secondary" className="uppercase tracking-wide">
                              {message.role}
                            </Badge>
                            {message.timestamp ? (
                              <span className="text-xs text-foreground/60">
                                {formatAbsolute(message.timestamp)}
                              </span>
                            ) : null}
                            <span className="text-xs text-foreground/50">#{index + 1}</span>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="gap-2 text-xs text-foreground/70"
                            onClick={() => handleCopyMessage(message.content)}
                          >
                            <Clipboard className="h-3.5 w-3.5" /> Copy
                          </Button>
                        </div>
                        <Separator className="bg-white/10" />
                        <p className={cn('whitespace-pre-wrap text-sm text-foreground/80', 'break-words')}>{message.content}</p>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </GlassPanel>
            </>
          ) : (
            <EmptyState
              title="Select a conversation"
              description="Choose a transcript from the archive to inspect its metadata and full history."
            />
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

function formatAbsolute(value?: string | null) {
  if (!value) {
    return '—';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}
