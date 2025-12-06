import type { StoragePresignDownloadResponse } from '@/lib/api/client/types.gen';
import { apiV1Path } from '@/lib/apiPaths';

const STORAGE_DOWNLOAD_ROUTE = (objectId: string) =>
  apiV1Path(`/storage/objects/${encodeURIComponent(objectId)}/download-url`);

/**
 * Fetch a presigned download URL for a storage object via the Next proxy route.
 */
export async function getAttachmentDownloadUrl(
  objectId: string,
): Promise<StoragePresignDownloadResponse> {
  const response = await fetch(STORAGE_DOWNLOAD_ROUTE(objectId), {
    method: 'GET',
    cache: 'no-store',
  });

  const body = await response
    .clone()
    .text()
    .catch(() => '');

  if (!response.ok) {
    let parsed: { message?: string } = {};
    if (body) {
      try {
        parsed = JSON.parse(body) as { message?: string };
      } catch {
        parsed = {};
      }
    }
    const message = parsed.message || `Failed to fetch download URL (HTTP ${response.status})`;
    throw new Error(message);
  }

  if (!body) {
    throw new Error('Empty download URL response.');
  }

  try {
    return JSON.parse(body) as StoragePresignDownloadResponse;
  } catch {
    throw new Error('Failed to parse download URL response.');
  }
}
