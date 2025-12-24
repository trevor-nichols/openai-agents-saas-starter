'use client';

import { useCallback, useState } from 'react';

import { useToast } from '@/components/ui/use-toast';
import { usePresignUpload } from '@/lib/queries/storageObjects';
import { useUploadVectorStoreFile } from '@/lib/queries/vectorStores';
import { uploadFileToPresignedUrl } from '@/lib/storage/upload';

import { VECTOR_STORE_UPLOAD_SOURCE } from '../constants';

interface VectorStoreUploadParams {
  vectorStoreId: string | null;
  agentKey: string | null;
  conversationId: string | null;
}

export function useVectorStoreUpload({
  vectorStoreId,
  agentKey,
  conversationId,
}: VectorStoreUploadParams) {
  const { error: showErrorToast, success: showSuccessToast } = useToast();
  const presignUpload = usePresignUpload();
  const uploadVectorStoreFile = useUploadVectorStoreFile();
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  const resetStatus = useCallback(() => setUploadStatus(null), []);

  const isUploading = presignUpload.isPending || uploadVectorStoreFile.isPending;

  const upload = useCallback(
    async (file: File | null) => {
      if (!vectorStoreId) {
        showErrorToast({
          title: 'Select a vector store',
          description: 'Choose a destination store.',
        });
        return false;
      }
      if (!file) {
        showErrorToast({ title: 'Choose a file first', description: 'Select a file to upload.' });
        return false;
      }

      try {
        setUploadStatus('Requesting upload URL…');
        const presign = await presignUpload.mutateAsync({
          filename: file.name,
          mime_type: file.type || 'application/octet-stream',
          size_bytes: file.size,
          conversation_id: conversationId,
          agent_key: agentKey,
          metadata: {
            source: VECTOR_STORE_UPLOAD_SOURCE,
          },
        });

        setUploadStatus('Uploading file…');
        await uploadFileToPresignedUrl(presign, file);

        setUploadStatus('Indexing in vector store…');
        await uploadVectorStoreFile.mutateAsync({
          vectorStoreId,
          body: {
            object_id: presign.object_id,
            attributes: { filename: file.name },
          },
        });

        setUploadStatus('Upload complete');
        showSuccessToast({
          title: 'File uploaded',
          description: `${file.name} is now attached to the vector store.`,
        });
        return true;
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Upload failed';
        setUploadStatus(null);
        showErrorToast({ title: 'Upload failed', description: message });
        return false;
      }
    },
    [
      agentKey,
      conversationId,
      presignUpload,
      showErrorToast,
      showSuccessToast,
      uploadVectorStoreFile,
      vectorStoreId,
    ],
  );

  return {
    upload,
    isUploading,
    uploadStatus,
    resetStatus,
  };
}
