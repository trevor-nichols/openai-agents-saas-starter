'use client';

import { Button } from '@/components/ui/button';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import { useDeleteVectorStoreFile, useVectorStoreFilesQuery } from '@/lib/queries/vectorStores';

import { VectorStoreUploadForm } from './VectorStoreUploadForm';

interface VectorStoreFilesPanelProps {
  vectorStoreId: string;
}

export function VectorStoreFilesPanel({ vectorStoreId }: VectorStoreFilesPanelProps) {
  const filesQuery = useVectorStoreFilesQuery(vectorStoreId, true);
  const deleteFile = useDeleteVectorStoreFile(vectorStoreId);

  return (
    <div className="space-y-2 rounded-lg border border-white/5 bg-white/5 p-3">
      <div className="flex items-center justify-between">
        <div className="text-sm font-semibold">Files</div>
        <Button
          size="sm"
          variant="outline"
          onClick={() => filesQuery.refetch()}
          disabled={filesQuery.isLoading}
        >
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
            <div
              key={file.id}
              className="flex items-center justify-between rounded-md border border-white/5 px-3 py-2 text-sm"
            >
              <span>{file.filename}</span>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => deleteFile.mutate(file.id)}
                disabled={deleteFile.isPending}
              >
                Remove file
              </Button>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState title="No files" description="Attach files to index them." />
      )}

      <VectorStoreUploadForm vectorStoreId={vectorStoreId} />
    </div>
  );
}
