import { vi } from 'vitest';

import type { AssetDownloadResponse } from '@/lib/api/client/types.gen';

import { GET } from './route';

const getAssetDownloadUrl = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/assets', () => ({
  getAssetDownloadUrl,
}));

describe('/api/assets/[assetId]/download-url route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns a presigned download payload', async () => {
    const payload: AssetDownloadResponse = {
      asset_id: 'asset-1',
      storage_object_id: 'obj-1',
      download_url: 'https://example.com/download',
      method: 'GET',
      headers: {},
      expires_in_seconds: 900,
    };
    getAssetDownloadUrl.mockResolvedValueOnce(payload);

    const response = await GET(new Request('http://localhost/api/v1/assets/asset-1/download-url'), {
      params: Promise.resolve({ assetId: 'asset-1' }),
    });

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(payload);
    expect(getAssetDownloadUrl).toHaveBeenCalledWith('asset-1');
  });

  it('returns 401 when missing access token error surfaces', async () => {
    getAssetDownloadUrl.mockRejectedValueOnce(new Error('Missing access token'));

    const response = await GET(new Request('http://localhost/api/v1/assets/asset-1/download-url'), {
      params: Promise.resolve({ assetId: 'asset-1' }),
    });

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({ message: 'Missing access token' });
  });

  it('returns 404 when asset is missing', async () => {
    getAssetDownloadUrl.mockRejectedValueOnce(new Error('Asset not found.'));

    const response = await GET(new Request('http://localhost/api/v1/assets/missing/download-url'), {
      params: Promise.resolve({ assetId: 'missing' }),
    });

    expect(response.status).toBe(404);
    await expect(response.json()).resolves.toEqual({ message: 'Asset not found.' });
  });
});
