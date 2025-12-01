import { vi } from 'vitest';
import type { NextRequest } from 'next/server';
import type { StoragePresignDownloadResponse } from '@/lib/api/client/types.gen';

import { GET } from './route';

const getServerApiClient = vi.hoisted(() => vi.fn());
const getDownloadUrlApiV1StorageObjectsObjectIdDownloadUrlGet = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/apiClient', () => ({
  getServerApiClient,
}));

vi.mock('@/lib/api/client/sdk.gen', () => ({
  getDownloadUrlApiV1StorageObjectsObjectIdDownloadUrlGet,
}));

describe('/api/storage/objects/[objectId]/download-url route', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns presigned download payload on success', async () => {
    const payload: StoragePresignDownloadResponse = {
      object_id: 'obj-1',
      download_url: 'https://example.com/presign',
      method: 'GET',
      headers: {},
      bucket: 'bkt',
      object_key: 'path/file',
      expires_in_seconds: 300,
    };

    getServerApiClient.mockResolvedValue({
      client: {},
      auth: vi.fn(),
    });
    getDownloadUrlApiV1StorageObjectsObjectIdDownloadUrlGet.mockResolvedValue({
      data: payload,
    });

    const request = {} as NextRequest;
    const response = await GET(request, { params: Promise.resolve({ objectId: 'obj-1' }) });

    expect(getDownloadUrlApiV1StorageObjectsObjectIdDownloadUrlGet).toHaveBeenCalledWith(
      expect.objectContaining({
        path: { object_id: 'obj-1' },
      }),
    );
    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(payload);
  });

  it('maps missing token errors to 401', async () => {
    getServerApiClient.mockRejectedValue(new Error('Missing access token'));

    const request = {} as NextRequest;
    const response = await GET(request, { params: Promise.resolve({ objectId: 'obj-1' }) });

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({ message: 'Missing access token' });
  });
});
