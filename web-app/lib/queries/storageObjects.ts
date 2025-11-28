import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { createPresignedUpload, deleteStorageObject, listStorageObjects } from '@/lib/api/storageObjects';
import type { StoragePresignUploadRequest } from '@/lib/api/client/types.gen';
import { queryKeys } from './keys';

export function useStorageObjectsQuery(params?: { limit?: number; offset?: number; conversationId?: string | null }) {
  return useQuery({
    queryKey: queryKeys.storage.objects(params ?? {}),
    queryFn: () => listStorageObjects(params),
  });
}

export function useDeleteStorageObject() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (objectId: string) => deleteStorageObject(objectId),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: queryKeys.storage.all }).catch(() => {});
    },
  });
}

export function usePresignUpload() {
  return useMutation({
    mutationFn: (payload: StoragePresignUploadRequest) => createPresignedUpload(payload),
  });
}
