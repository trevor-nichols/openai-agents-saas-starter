'use server';

import {
  createPresignedUploadApiV1StorageObjectsUploadUrlPost,
  deleteObjectApiV1StorageObjectsObjectIdDelete,
  getDownloadUrlApiV1StorageObjectsObjectIdDownloadUrlGet,
  listObjectsApiV1StorageObjectsGet,
} from '@/lib/api/client/sdk.gen';
import type {
  StorageObjectListResponse,
  StoragePresignDownloadResponse,
  StoragePresignUploadRequest,
  StoragePresignUploadResponse,
} from '@/lib/api/client/types.gen';

import { getServerApiClient } from '../apiClient';

/**
 * Fetch a presigned download URL for a storage object using server credentials.
 */
export async function getPresignedDownloadUrl(
  objectId: string,
): Promise<StoragePresignDownloadResponse> {
  const { client, auth } = await getServerApiClient();

  const response = await getDownloadUrlApiV1StorageObjectsObjectIdDownloadUrlGet({
    client,
    auth,
    path: { object_id: objectId },
    responseStyle: 'fields',
    throwOnError: true,
  });

  if (!response.data) {
    throw new Error('Download URL payload missing.');
  }

  return response.data;
}

export interface StorageObjectListParams {
  limit?: number;
  offset?: number;
  conversationId?: string | null;
}

export async function listStorageObjects(
  params?: StorageObjectListParams,
): Promise<StorageObjectListResponse> {
  const { client, auth } = await getServerApiClient();
  const response = await listObjectsApiV1StorageObjectsGet({
    client,
    auth,
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

export async function createPresignedUploadUrl(
  payload: StoragePresignUploadRequest,
): Promise<StoragePresignUploadResponse> {
  const { client, auth } = await getServerApiClient();
  const response = await createPresignedUploadApiV1StorageObjectsUploadUrlPost({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    body: payload,
  });

  if (!response.data) {
    throw new Error('Presign response missing data.');
  }

  return response.data;
}

export async function deleteStorageObject(objectId: string): Promise<void> {
  if (!objectId) {
    throw new Error('objectId is required.');
  }

  const { client, auth } = await getServerApiClient();
  await deleteObjectApiV1StorageObjectsObjectIdDelete({
    client,
    auth,
    throwOnError: true,
    responseStyle: 'fields',
    path: { object_id: objectId },
  });
}
