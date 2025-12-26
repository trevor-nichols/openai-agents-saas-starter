'use client';

import { useCallback, useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/components/ui/use-toast';
import { usePresignUpload } from '@/lib/queries/storageObjects';
import { useUploadVectorStoreFile, useVectorStoresQuery } from '@/lib/queries/vectorStores';
import { uploadFileToPresignedUrl } from '@/lib/storage/upload';

interface VectorStoreUploadSectionProps {
  agentKey: string;
  enabled: boolean;
}

export function VectorStoreUploadSection({ agentKey, enabled }: VectorStoreUploadSectionProps) {
  const vectorStoresQuery = useVectorStoresQuery({ enabled });
  const presignUpload = usePresignUpload();
  const uploadVectorStoreFile = useUploadVectorStoreFile();
  const { success: showSuccessToast, error: showErrorToast } = useToast();

  const [selectedStoreId, setSelectedStoreId] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [fileInputKey, setFileInputKey] = useState(0);

  const vectorStores = useMemo(() => vectorStoresQuery.data?.items ?? [], [vectorStoresQuery.data]);
  const isUploading = presignUpload.isPending || uploadVectorStoreFile.isPending;

  const effectiveStoreId = useMemo(() => {
    if (!enabled) {
      return null;
    }
    if (selectedStoreId && vectorStores.some((store) => store.id === selectedStoreId)) {
      return selectedStoreId;
    }
    return vectorStores[0]?.id ?? null;
  }, [enabled, selectedStoreId, vectorStores]);

  const handleUpload = useCallback(async () => {
    if (!selectedFile) {
      showErrorToast({ title: 'Choose a file first', description: 'Select a file to upload.' });
      return;
    }
    if (!effectiveStoreId) {
      showErrorToast({ title: 'Select a vector store', description: 'Choose a destination store.' });
      return;
    }

    try {
      setStatus('Requesting upload URL…');
      const presign = await presignUpload.mutateAsync({
        filename: selectedFile.name,
        mime_type: selectedFile.type || 'application/octet-stream',
        size_bytes: selectedFile.size,
        agent_key: agentKey,
        metadata: {
          source: 'chat_vector_store',
          agent_key: agentKey,
        },
      });

      setStatus('Uploading file…');
      await uploadFileToPresignedUrl(presign, selectedFile);

      setStatus('Indexing in vector store…');
      await uploadVectorStoreFile.mutateAsync({
        vectorStoreId: effectiveStoreId,
        body: {
          object_id: presign.object_id,
          agent_key: agentKey,
          attributes: { filename: selectedFile.name },
        },
      });

      setStatus('Upload complete');
      showSuccessToast({
        title: 'File uploaded',
        description: `${selectedFile.name} is now available for file_search.`,
      });
      setSelectedFile(null);
      setFileInputKey((prev) => prev + 1);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Upload failed';
      showErrorToast({ title: 'Upload failed', description: message });
      setStatus(null);
    }
  }, [
    agentKey,
    presignUpload,
    selectedFile,
    effectiveStoreId,
    showErrorToast,
    showSuccessToast,
    uploadVectorStoreFile,
  ]);

  if (!enabled) {
    return null;
  }

  return (
    <div className="space-y-2">
      <div>
        <Label className="text-xs">Vector store uploads</Label>
        <p className="text-xs text-muted-foreground">
          Upload files to the selected agent&apos;s file_search store.
        </p>
      </div>

      {vectorStoresQuery.isLoading ? (
        <Skeleton className="h-9 w-full" />
      ) : vectorStoresQuery.error ? (
        <p className="text-xs text-destructive">
          {vectorStoresQuery.error instanceof Error
            ? vectorStoresQuery.error.message
            : 'Vector stores unavailable.'}
        </p>
      ) : vectorStores.length === 0 ? (
        <p className="text-xs text-muted-foreground">
          No vector stores available. Create one in Storage admin.
        </p>
      ) : (
        <Select
          value={effectiveStoreId ?? undefined}
          onValueChange={(value) => setSelectedStoreId(value)}
          disabled={isUploading}
        >
          <SelectTrigger className="h-9 text-xs">
            <SelectValue placeholder="Select vector store" />
          </SelectTrigger>
          <SelectContent>
            {vectorStores.map((store) => (
              <SelectItem key={store.id} value={store.id}>
                {store.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}

      <div className="space-y-2">
        <Input
          key={fileInputKey}
          type="file"
          disabled={isUploading || vectorStores.length === 0}
          onChange={(event) => {
            const file = event.target.files?.[0] ?? null;
            setSelectedFile(file);
          }}
        />
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            onClick={() => void handleUpload()}
            disabled={isUploading || !selectedFile || !effectiveStoreId}
          >
            {isUploading ? 'Uploading…' : 'Upload file'}
          </Button>
          {status ? <span className="text-xs text-muted-foreground">{status}</span> : null}
        </div>
      </div>
    </div>
  );
}
