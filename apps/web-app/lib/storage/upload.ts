import type { StoragePresignUploadResponse } from '@/lib/api/client/types.gen';

/**
 * Upload a file to the presigned URL returned by the API.
 * Throws if the upload fails (non-2xx response).
 */
export async function uploadFileToPresignedUrl(
  presign: StoragePresignUploadResponse,
  file: File,
): Promise<void> {
  const headers = new Headers(presign.headers ?? {});
  // Provide a sensible content type if the backend didn't include one.
  if (file.type && !headers.has('Content-Type')) {
    headers.set('Content-Type', file.type);
  }

  const method = presign.method?.toUpperCase() || 'PUT';
  const response = await fetch(presign.upload_url, {
    method,
    headers,
    body: file,
  });

  if (!response.ok) {
    const text = await response.text().catch(() => '');
    const reason = text || response.statusText || 'upload failed';
    throw new Error(`Upload failed (${response.status}): ${reason}`);
  }
}
