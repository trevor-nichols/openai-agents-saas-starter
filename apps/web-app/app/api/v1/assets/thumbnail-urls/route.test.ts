import { vi } from 'vitest';

import type { AssetThumbnailUrlsResponse } from '@/lib/api/client/types.gen';

import { POST } from './route';

const getAssetThumbnailUrls = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/assets', () => ({
  getAssetThumbnailUrls,
}));

describe('/api/assets/thumbnail-urls route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns thumbnail URLs for asset ids', async () => {
    const payload: AssetThumbnailUrlsResponse = {
      items: [],
      missing_asset_ids: [],
      unsupported_asset_ids: [],
    };
    getAssetThumbnailUrls.mockResolvedValueOnce(payload);

    const response = await POST(
      new Request('http://localhost/api/v1/assets/thumbnail-urls', {
        method: 'POST',
        body: JSON.stringify({ asset_ids: ['asset-1'] }),
      }),
    );

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(payload);
    expect(getAssetThumbnailUrls).toHaveBeenCalledWith(['asset-1']);
  });

  it('returns 400 when payload is invalid', async () => {
    const response = await POST(
      new Request('http://localhost/api/v1/assets/thumbnail-urls', {
        method: 'POST',
        body: JSON.stringify({ asset_ids: [] }),
      }),
    );

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ message: 'asset_ids must not be empty' });
  });

  it('returns 401 when missing access token error surfaces', async () => {
    getAssetThumbnailUrls.mockRejectedValueOnce(new Error('Missing access token'));

    const response = await POST(
      new Request('http://localhost/api/v1/assets/thumbnail-urls', {
        method: 'POST',
        body: JSON.stringify({ asset_ids: ['asset-1'] }),
      }),
    );

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({ message: 'Missing access token' });
  });
});
