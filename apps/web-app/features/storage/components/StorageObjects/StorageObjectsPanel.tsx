'use client';

import { Download, Filter, Loader2, RefreshCw, Trash2 } from 'lucide-react';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { GlassPanel } from '@/components/ui/foundation';
import { Input } from '@/components/ui/input';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useToast } from '@/components/ui/use-toast';
import { cn } from '@/lib/utils';
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
  const [showUpload, setShowUpload] = useState(false);

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
    <GlassPanel className="p-0 overflow-hidden flex flex-col">
      {/* Header & Toolbar */}
      <div className="border-b border-border/50 bg-muted/20 p-4 space-y-4">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="text-sm font-semibold tracking-tight">Storage Objects</h3>
            <p className="text-xs text-muted-foreground">Manage files, downloads, and presigned uploads.</p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant={showUpload ? 'secondary' : 'outline'}
              onClick={() => setShowUpload(!showUpload)}
            >
              {showUpload ? 'Cancel Upload' : 'Upload File'}
            </Button>
            <Button
              size="icon"
              variant="ghost"
              onClick={() => storageQuery.refetch()}
              disabled={storageQuery.isFetching}
              title="Refresh"
            >
              <RefreshCw className={cn('h-4 w-4', storageQuery.isFetching && 'animate-spin')} />
            </Button>
          </div>
        </div>

        {/* Upload Form Expansion */}
        {showUpload && (
          <div className="animate-in slide-in-from-top-2 fade-in">
            <UploadObjectForm onUploaded={() => {
              storageQuery.refetch();
              setShowUpload(false);
            }} />
          </div>
        )}

        {/* Filter Bar */}
        <div className="flex items-center gap-2">
          <div className="relative flex-1 max-w-sm">
            <Filter className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              value={conversationInput}
              onChange={(e) => setConversationInput(e.target.value)}
              placeholder="Filter by Conversation ID..."
              className="pl-9 h-9 text-xs"
              onKeyDown={(e) => e.key === 'Enter' && applyConversationFilter()}
            />
          </div>
          <Button 
            size="sm" 
            variant="secondary" 
            onClick={applyConversationFilter}
            disabled={!conversationInput && !conversationFilter}
            className="h-9 px-3"
          >
            Filter
          </Button>
          {(conversationFilter || conversationInput) && (
            <Button 
              size="sm" 
              variant="ghost" 
              onClick={clearConversationFilter}
              className="h-9 px-3"
            >
              Clear
            </Button>
          )}
          <div className="ml-auto text-xs text-muted-foreground">
            {items.length} object{items.length === 1 ? '' : 's'}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="relative min-h-[200px]">
        {storageQuery.isLoading ? (
          <div className="p-4">
            <SkeletonPanel lines={5} />
          </div>
        ) : storageQuery.isError ? (
          <div className="p-8">
            <ErrorState title="Failed to load objects" />
          </div>
        ) : items.length === 0 ? (
          <div className="p-8">
            <EmptyState 
              title="No storage objects found" 
              description={conversationFilter ? "Try clearing the filter." : "Upload a file to get started."} 
            />
          </div>
        ) : (
          <div className="border-t border-border/10">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent border-border/50">
                  <TableHead className="w-[40%]">Filename</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Context</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((obj) => (
                  <TableRow key={obj.id} className="border-border/50">
                    <TableCell className="font-medium text-foreground">
                      {obj.filename ?? obj.object_key}
                      <div className="text-[10px] text-muted-foreground font-mono mt-0.5 truncate max-w-[200px]">
                        {obj.object_key}
                      </div>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {obj.mime_type ?? 'unknown'}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground font-mono">
                      {obj.size_bytes ? (obj.size_bytes / 1024).toFixed(1) + ' KB' : '0 B'}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground max-w-[150px] truncate">
                      {obj.conversation_id ? (
                        <span title={obj.conversation_id} className="font-mono bg-muted/30 px-1 py-0.5 rounded">
                          {obj.conversation_id.slice(0, 8)}...
                        </span>
                      ) : (
                        <span className="opacity-50">—</span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => handleDownload(obj.id)}
                          disabled={downloadingId === obj.id}
                          className="h-8 w-8 text-muted-foreground hover:text-foreground"
                          title="Download"
                        >
                          {downloadingId === obj.id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Download className="h-4 w-4" />
                          )}
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => deleteObject.mutate(obj.id)}
                          disabled={deleteObject.isPending}
                          className="h-8 w-8 text-muted-foreground hover:text-destructive"
                          title="Delete"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>

      {storageQuery.hasNextPage && (
        <div className="p-4 border-t border-border/50 flex justify-center bg-muted/10">
          <Button
            size="sm"
            variant="outline"
            onClick={() => storageQuery.fetchNextPage()}
            disabled={storageQuery.isFetchingNextPage}
            className="w-full max-w-xs"
          >
            {storageQuery.isFetchingNextPage ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Loading...
              </>
            ) : (
              'Load More'
            )}
          </Button>
        </div>
      )}
    </GlassPanel>
  );
}
