// File Path: features/chat/components/ConversationDetailDrawer.tsx
// Description: Sheet showing conversation metadata, exports, and delete controls.

'use client';

import { useMemo, useState } from 'react';
import { Download, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { GlassPanel, InlineTag, KeyValueList, SectionHeader } from '@/components/ui/foundation';
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { Separator } from '@/components/ui/separator';
import { SkeletonPanel, ErrorState } from '@/components/ui/states';
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useConversationDetail } from '@/lib/queries/conversations';
import { formatClockTime } from '@/lib/utils/time';

interface ConversationDetailDrawerProps {
  conversationId: string | null;
  open: boolean;
  onOpenChange: (value: boolean) => void;
  onDeleteConversation: (conversationId: string) => Promise<void>;
}

export function ConversationDetailDrawer({
  conversationId,
  open,
  onOpenChange,
  onDeleteConversation,
}: ConversationDetailDrawerProps) {
  const {
    conversationHistory,
    isLoadingDetail,
    detailError,
    refetchDetail,
  } = useConversationDetail(conversationId);
  const [isDeleting, setIsDeleting] = useState(false);

  const metadata = useMemo(() => {
    if (!conversationHistory) return [];
    return [
      { label: 'Conversation ID', value: conversationHistory.conversation_id },
      { label: 'Created', value: formatClockTime(conversationHistory.created_at) },
      { label: 'Updated', value: formatClockTime(conversationHistory.updated_at) },
      { label: 'Message count', value: `${conversationHistory.messages.length}` },
    ];
  }, [conversationHistory]);

  const latestMessages = useMemo(() => {
    if (!conversationHistory) return [];
    return conversationHistory.messages.slice(-6);
  }, [conversationHistory]);

  const handleExport = () => {
    if (!conversationHistory) return;
    const payload = JSON.stringify(conversationHistory, null, 2);
    const blob = new Blob([payload], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `conversation-${conversationHistory.conversation_id}.json`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    toast.success('Conversation exported to JSON.');
  };

  const handleDelete = async () => {
    if (!conversationId) return;
    setIsDeleting(true);
    try {
      await onDeleteConversation(conversationId);
      toast.success('Conversation deleted.');
      onOpenChange(false);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full max-w-md">
        <SheetHeader>
          <SheetTitle>Conversation details</SheetTitle>
          <SheetDescription>Metadata, audit log, and export/delete controls.</SheetDescription>
        </SheetHeader>

        {isLoadingDetail ? (
          <SkeletonPanel lines={8} className="m-4" />
        ) : detailError ? (
          <div className="m-4">
            <ErrorState title="Unable to load detail" message={detailError} onRetry={refetchDetail} />
          </div>
        ) : (
          <>
            <GlassPanel className="m-4 space-y-4">
              <SectionHeader
                eyebrow="Metadata"
                title={metadata[0]?.value ?? 'Untitled conversation'}
                description={conversationId ? `ID · ${conversationId}` : 'Select a conversation to view detail.'}
                actions={
                  <InlineTag tone="default">{latestMessages.length ? 'Active' : 'Idle'}</InlineTag>
                }
              />
              <KeyValueList columns={2} items={metadata.map((item) => ({ label: item.label, value: item.value }))} />
            </GlassPanel>

            <div className="px-4">
              <SectionHeader eyebrow="Audit" title="Recent messages" description="Last six entries from this thread." />
              {latestMessages.length === 0 ? (
                <p className="mt-2 text-xs text-foreground/70">
                  This conversation has no messages yet.
                </p>
              ) : (
                <Table className="mt-3 text-xs">
                  <TableHeader>
                    <TableRow>
                      <TableHead>Role</TableHead>
                      <TableHead>Content</TableHead>
                      <TableHead className="text-right">Timestamp</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {latestMessages.map((message, index) => (
                      <TableRow key={`${message.timestamp ?? index}-${index}`}>
                        <TableCell>
                          <InlineTag tone={message.role === 'user' ? 'positive' : 'default'}>
                            {message.role === 'system' ? 'System' : message.role === 'assistant' ? 'Agent' : 'You'}
                          </InlineTag>
                        </TableCell>
                        <TableCell className="text-foreground/80">
                          <p className="line-clamp-2 text-sm">{message.content}</p>
                        </TableCell>
                        <TableCell className="text-right text-foreground/60">
                          {message.timestamp ? formatClockTime(message.timestamp) : '—'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                  <TableCaption className="text-xs text-foreground/50">
                    Full history available in the backend audit log.
                  </TableCaption>
                </Table>
              )}
            </div>
          </>
        )}

        <Separator className="mt-6" />

        <SheetFooter className="flex flex-col gap-2 px-4 py-4">
          <Button onClick={handleExport} variant="outline" disabled={!conversationHistory}>
            <Download className="mr-2 h-4 w-4" />
            Export JSON
          </Button>
          <Button onClick={handleDelete} variant="destructive" disabled={isDeleting || !conversationId}>
            <Trash2 className="mr-2 h-4 w-4" />
            {isDeleting ? 'Deleting…' : 'Delete conversation'}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
