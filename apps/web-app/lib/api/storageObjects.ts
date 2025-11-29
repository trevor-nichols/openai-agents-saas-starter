import {
  createPresignedUploadApiV1StorageObjectsUploadUrlPost,
  deleteObjectApiV1StorageObjectsObjectIdDelete,
  listObjectsApiV1StorageObjectsGet,
} from '@/lib/api/client/sdk.gen';
import type {
  StorageObjectListResponse,
  StoragePresignUploadRequest,
  StoragePresignUploadResponse,
} from '@/lib/api/client/types.gen';
import { USE_API_MOCK } from '@/lib/config';
import { mockPresignUpload, mockStorageObjects } from '@/lib/storage/mock';
import { client } from './config';

export async function listStorageObjects(params?: { limit?: number; offset?: number; conversationId?: string | null }) {
  if (USE_API_MOCK) {
    const resp: StorageObjectListResponse = { items: mockStorageObjects, next_offset: null };
    return resp;
  }
  const response = await listObjectsApiV1StorageObjectsGet({
    client,
    responseStyle: 'fields',
    throwOnError: true,
    query: {
      limit: params?.limit,
      offset: params?.offset,
      conversation_id: params?.conversationId ?? undefined,
    },
  });
  return response.data ?? { items: [], next_offset: null };
}

export async function deleteStorageObject(objectId: string) {
  if (USE_API_MOCK) {
    return;
  }
  await deleteObjectApiV1StorageObjectsObjectIdDelete({
    client,
    throwOnError: true,
    path: { object_id: objectId },
  });
}

export async function createPresignedUpload(payload: StoragePresignUploadRequest): Promise<StoragePresignUploadResponse> {
  if (USE_API_MOCK) {
    return mockPresignUpload;
  }
  const response = await createPresignedUploadApiV1StorageObjectsUploadUrlPost({
    client,
    throwOnError: true,
    responseStyle: 'fields',
    body: payload,
  });
  if (!response.data) throw new Error('Presign upload missing data');
  return response.data;
}
