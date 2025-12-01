import type {
  StorageObjectListResponse,
  StoragePresignUploadRequest,
  StoragePresignUploadResponse,
} from '@/lib/api/client/types.gen';
import { USE_API_MOCK } from '@/lib/config';
import { mockPresignUpload, mockStorageObjects } from '@/lib/storage/mock';

async function parseJson<T>(response: Response): Promise<T> {
  try {
    return (await response.json()) as T;
  } catch {
    throw new Error('Failed to parse storage response');
  }
}

function buildError(response: Response, fallback: string): Error {
  return new Error(fallback || `Request failed with ${response.status}`);
}

export async function listStorageObjects(params?: {
  limit?: number;
  offset?: number;
  conversationId?: string | null;
}): Promise<StorageObjectListResponse> {
  if (USE_API_MOCK) {
    const resp: StorageObjectListResponse = { items: mockStorageObjects, next_offset: null };
    return resp;
  }

  const query = new URLSearchParams();
  if (params?.limit) query.set('limit', String(params.limit));
  if (params?.offset !== undefined) query.set('offset', String(params.offset));
  if (params?.conversationId) query.set('conversation_id', params.conversationId);

  const res = await fetch(`/api/storage/objects${query.size ? `?${query.toString()}` : ''}`, {
    cache: 'no-store',
  });

  if (!res.ok) throw buildError(res, 'Failed to load storage objects');
  return parseJson<StorageObjectListResponse>(res);
}

export async function deleteStorageObject(objectId: string) {
  if (USE_API_MOCK) return;

  const res = await fetch(`/api/storage/objects/${encodeURIComponent(objectId)}`, { method: 'DELETE' });
  if (!res.ok) throw buildError(res, 'Failed to delete storage object');
}

export async function createPresignedUpload(
  payload: StoragePresignUploadRequest,
): Promise<StoragePresignUploadResponse> {
  if (USE_API_MOCK) return mockPresignUpload;

  const res = await fetch('/api/storage/objects/upload-url', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) throw buildError(res, 'Failed to presign upload');
  return parseJson<StoragePresignUploadResponse>(res);
}
