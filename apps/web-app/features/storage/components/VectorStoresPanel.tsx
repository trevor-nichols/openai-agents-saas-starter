'use client';

import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { GlassPanel } from '@/components/ui/foundation';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import {
  useAttachVectorStoreFile,
  useCreateVectorStore,
  useDeleteVectorStore,
  useDeleteVectorStoreFile,
  useVectorStoreFilesQuery,
  useVectorStoresQuery,
} from '@/lib/queries/vectorStores';

export function VectorStoresPanel() {
  const vectorStoresQuery = useVectorStoresQuery();
  const createVector = useCreateVectorStore();
  const deleteVector = useDeleteVectorStore();
  const [selectedVs, setSelectedVs] = useState<string | null>(null);
  const filesQuery = useVectorStoreFilesQuery(selectedVs ?? 'vs-placeholder', Boolean(selectedVs));
  const attachFile = useAttachVectorStoreFile(selectedVs ?? '');
  const deleteFile = useDeleteVectorStoreFile(selectedVs ?? '');

  const [newVsName, setNewVsName] = useState('');
  const [fileIdInput, setFileIdInput] = useState('');

  return (
    <GlassPanel className="p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold">Vector Stores</h3>
          <p className="text-xs text-foreground/60">Create stores and attach uploaded files.</p>
        </div>
        <Button size="sm" variant="outline" onClick={() => vectorStoresQuery.refetch()} disabled={vectorStoresQuery.isLoading}>
          Refresh
        </Button>
      </div>

      <div className="flex gap-2 items-end">
        <div className="space-y-1">
          <Label className="text-xs text-foreground/70">Name</Label>
          <Input value={newVsName} onChange={(e) => setNewVsName(e.target.value)} placeholder="New vector store" />
        </div>
        <Button
          size="sm"
          onClick={() => newVsName.trim() && createVector.mutate({ name: newVsName, description: null, metadata: null, expires_after: null })}
          disabled={createVector.isPending}
        >
          Create
        </Button>
      </div>

      {vectorStoresQuery.isLoading ? (
        <SkeletonPanel lines={6} />
      ) : vectorStoresQuery.isError ? (
        <ErrorState title="Failed to load vector stores" />
      ) : (vectorStoresQuery.data?.items?.length ?? 0) === 0 ? (
        <EmptyState title="No vector stores" description="Create a store to attach files." />
      ) : (
        <div className="grid gap-2">
          {(vectorStoresQuery.data?.items ?? []).map((vs) => (
            <div
              key={vs.id}
              className="rounded-lg border border-white/5 bg-white/5 p-3 flex items-center justify-between gap-3"
            >
              <div>
                <div className="font-semibold">{vs.name}</div>
                <div className="text-xs text-foreground/60">{vs.description ?? '—'}</div>
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant={selectedVs === vs.id ? 'default' : 'secondary'} onClick={() => setSelectedVs(vs.id)}>
                  {selectedVs === vs.id ? 'Selected' : 'Files'}
                </Button>
                <Button size="sm" variant="ghost" onClick={() => deleteVector.mutate(vs.id)} disabled={deleteVector.isPending}>
                  Delete
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedVs ? (
        <div className="space-y-2 rounded-lg border border-white/5 bg-white/5 p-3">
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold">Files</div>
            <Button size="sm" variant="outline" onClick={() => filesQuery.refetch()} disabled={filesQuery.isLoading}>
              Refresh
            </Button>
          </div>
          {filesQuery.isLoading ? (
            <SkeletonPanel lines={3} />
          ) : filesQuery.isError ? (
            <ErrorState title="Failed to load files" />
          ) : filesQuery.data?.items.length ? (
            <div className="space-y-2">
              {filesQuery.data.items.map((file) => (
                <div key={file.id} className="flex items-center justify-between rounded-md border border-white/5 px-3 py-2 text-sm">
                  <span>{file.filename}</span>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => selectedVs && deleteFile.mutate(file.id)}
                    disabled={deleteFile.isPending || !selectedVs}
                  >
                    Remove file
                  </Button>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="No files" description="Attach files to index them." />
          )}

          <div className="space-y-1">
            <Label className="text-xs text-foreground/70">Attach file (ID)</Label>
            <div className="flex gap-2">
              <Input
                placeholder="file_id"
                onChange={(e) => setFileIdInput(e.target.value)}
                value={fileIdInput}
                className="max-w-xs"
              />
              <Button
                size="sm"
                onClick={() =>
                  attachFile.mutate({
                    file_id: fileIdInput || 'file-id',
                    attributes: {},
                    chunking_strategy: null,
                    poll: false,
                  })
                }
                disabled={attachFile.isPending}
              >
                Attach
              </Button>
            </div>
          </div>
        </div>
      ) : null}
    </GlassPanel>
  );
}
