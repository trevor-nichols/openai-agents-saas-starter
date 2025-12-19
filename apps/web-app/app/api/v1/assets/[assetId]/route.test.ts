import { vi } from 'vitest';

import type { AssetResponse } from '@/lib/api/client/types.gen';

import { DELETE, GET } from './route';

const getAsset = vi.hoisted(() => vi.fn());
const deleteAsset = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/assets', () => ({
  getAsset,
  deleteAsset,
}));

describe('/api/assets/[assetId] route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns asset details on GET', async () => {
    const payload = {
      id: 'asset-1',
      storage_object_id: 'obj-1',
      asset_type: 'image',
    } satisfies AssetResponse;
    getAsset.mockResolvedValueOnce(payload);

    const response = await GET(new Request('http://localhost/api/v1/assets/asset-1'), {
      params: Promise.resolve({ assetId: 'asset-1' }),
    });

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(payload);
    expect(getAsset).toHaveBeenCalledWith('asset-1');
  });

  it('deletes asset on DELETE', async () => {
    deleteAsset.mockResolvedValueOnce(undefined);

    const response = await DELETE(new Request('http://localhost/api/v1/assets/asset-2'), {
      params: Promise.resolve({ assetId: 'asset-2' }),
    });

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({ success: true });
    expect(deleteAsset).toHaveBeenCalledWith('asset-2');
  });

  it('returns 404 when asset is missing', async () => {
    getAsset.mockRejectedValueOnce(new Error('Asset not found.'));

    const response = await GET(new Request('http://localhost/api/v1/assets/missing'), {
      params: Promise.resolve({ assetId: 'missing' }),
    });

    expect(response.status).toBe(404);
    await expect(response.json()).resolves.toEqual({ message: 'Asset not found.' });
  });

  it('returns 404 when delete target is missing', async () => {
    deleteAsset.mockRejectedValueOnce(new Error('Asset not found.'));

    const response = await DELETE(new Request('http://localhost/api/v1/assets/missing'), {
      params: Promise.resolve({ assetId: 'missing' }),
    });

    expect(response.status).toBe(404);
    await expect(response.json()).resolves.toEqual({ message: 'Asset not found.' });
  });
});
