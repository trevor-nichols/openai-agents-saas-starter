import { vi } from 'vitest';

import type { NextRequest } from 'next/server';
import type { StoragePresignDownloadResponse } from '@/lib/api/client/types.gen';

import { GET } from './route';

const getPresignedDownloadUrl = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/storage', () => ({
  getPresignedDownloadUrl,
}));

describe('/api/storage/objects/[objectId]/download-url route', () => {
  afterEach(() => {
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

    getPresignedDownloadUrl.mockResolvedValueOnce(payload);

    const request = {} as NextRequest;
    const response = await GET(request, { params: { objectId: 'obj-1' } });

    expect(getPresignedDownloadUrl).toHaveBeenCalledWith('obj-1');
    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(payload);
  });

  it('maps missing token errors to 401', async () => {
    getPresignedDownloadUrl.mockRejectedValueOnce(new Error('Missing access token'));

    const request = {} as NextRequest;
    const response = await GET(request, { params: { objectId: 'obj-1' } });

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({ message: 'Missing access token' });
  });
});
