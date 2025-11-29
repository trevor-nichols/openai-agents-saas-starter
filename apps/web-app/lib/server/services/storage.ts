'use server';

import { getDownloadUrlApiV1StorageObjectsObjectIdDownloadUrlGet } from '@/lib/api/client/sdk.gen';
import type { StoragePresignDownloadResponse } from '@/lib/api/client/types.gen';

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
