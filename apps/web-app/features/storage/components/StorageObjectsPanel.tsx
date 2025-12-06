'use client';

import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { GlassPanel } from '@/components/ui/foundation';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import { useToast } from '@/components/ui/use-toast';
import { getAttachmentDownloadUrl } from '@/lib/api/storage';
import {
  useDeleteStorageObject,
  useStorageObjectsInfiniteQuery,
} from '@/lib/queries/storageObjects';

import { UploadObjectForm } from './UploadObjectForm';

const PAGE_SIZE = 20;

export function StorageObjectsPanel() {
  const [conversationInput, setConversationInput] = useState('');
  const [conversationFilter, setConversationFilter] = useState<string | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const storageQuery = useStorageObjectsInfiniteQuery({
    limit: PAGE_SIZE,
    conversationId: conversationFilter,
  });
  const deleteObject = useDeleteStorageObject();
  const { error: showErrorToast } = useToast();

  const items = storageQuery.data?.pages.flatMap((page) => page.items ?? []) ?? [];

  const handleDownload = async (objectId: string) => {
    setDownloadingId(objectId);
    try {
      const presign = await getAttachmentDownloadUrl(objectId);
      window.open(presign.download_url, '_blank', 'noopener,noreferrer');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Download failed';
      showErrorToast({ title: 'Could not fetch link', description: message });
    } finally {
      setDownloadingId(null);
    }
  };

  const applyConversationFilter = () => {
    const trimmed = conversationInput.trim();
    setConversationFilter(trimmed || null);
  };

  const clearConversationFilter = () => {
    setConversationInput('');
    setConversationFilter(null);
  };

  return (
    <GlassPanel className="p-4 space-y-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h3 className="text-sm font-semibold">Storage Objects</h3>
          <p className="text-xs text-foreground/60">Presign uploads, browse stored files, fetch download links.</p>
        </div>
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => storageQuery.refetch()}
            disabled={storageQuery.isFetching}
          >
            Refresh
          </Button>
        </div>
      </div>

      <UploadObjectForm onUploaded={() => storageQuery.refetch()} />

      <div className="grid gap-3 md:grid-cols-[2fr_1fr] lg:grid-cols-[2fr_1fr_1fr]">
        <div className="space-y-1">
          <Label className="text-xs text-foreground/70">Conversation filter (UUID, optional)</Label>
          <div className="flex gap-2">
            <Input
              value={conversationInput}
              onChange={(e) => setConversationInput(e.target.value)}
              placeholder="conversation-id"
            />
            <Button size="sm" variant="secondary" onClick={applyConversationFilter}>
              Apply
            </Button>
            <Button size="sm" variant="ghost" onClick={clearConversationFilter} disabled={!conversationFilter && !conversationInput}>
              Clear
            </Button>
          </div>
        </div>
        <div className="space-y-1">
          <Label className="text-xs text-foreground/70">Total loaded</Label>
          <div className="rounded-md border border-white/5 bg-white/5 px-3 py-2 text-sm">
            {items.length} object{items.length === 1 ? '' : 's'}
          </div>
        </div>
      </div>

      {storageQuery.isLoading ? (
        <SkeletonPanel lines={6} />
      ) : storageQuery.isError ? (
        <ErrorState title="Failed to load storage objects" />
      ) : items.length === 0 ? (
        <EmptyState title="No objects" description="Upload a file to get started." />
      ) : (
        <div className="divide-y divide-white/5 rounded-lg border border-white/5">
          {items.map((obj) => (
            <div key={obj.id} className="flex flex-col gap-2 px-3 py-3 text-sm md:flex-row md:items-center md:justify-between">
              <div className="space-y-1">
                <div className="font-semibold text-foreground">{obj.filename ?? obj.object_key}</div>
                <div className="text-foreground/60 text-xs">
                  {obj.mime_type ?? 'unknown'} • {obj.size_bytes ?? 0} bytes
                  {obj.conversation_id ? ` • conversation ${obj.conversation_id}` : ''}
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => handleDownload(obj.id)}
                  disabled={downloadingId === obj.id}
                >
                  {downloadingId === obj.id ? 'Fetching…' : 'Download'}
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => deleteObject.mutate(obj.id)}
                  disabled={deleteObject.isPending}
                >
                  Delete
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {storageQuery.hasNextPage ? (
        <Button
          size="sm"
          variant="outline"
          onClick={() => storageQuery.fetchNextPage()}
          disabled={storageQuery.isFetchingNextPage}
        >
          {storageQuery.isFetchingNextPage ? 'Loading…' : 'Load more'}
        </Button>
      ) : null}
    </GlassPanel>
  );
}
