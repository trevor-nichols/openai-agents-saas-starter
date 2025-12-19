import { afterEach, beforeEach, describe, expect, it, vi, type Mock } from 'vitest';

import { getAssetThumbnailUrls } from '@/lib/api/assets';

const originalFetch = global.fetch;

describe('getAssetThumbnailUrls', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    if (originalFetch) {
      global.fetch = originalFetch;
    } else {
      // @ts-expect-error cleanup mocked fetch reference
      delete global.fetch;
    }
  });

  it('returns empty payload when no asset ids are provided', async () => {
    const result = await getAssetThumbnailUrls([]);

    expect(result).toEqual({ items: [], missing_asset_ids: [], unsupported_asset_ids: [] });
  });

  it('batches thumbnail requests over the 200 id limit', async () => {
    const ids = Array.from({ length: 201 }, (_, index) => `asset-${index + 1}`);
    global.fetch = vi.fn().mockImplementation(async (_input, init) => {
      const body = JSON.parse(String(init?.body ?? '{}')) as { asset_ids?: string[] };
      const items =
        body.asset_ids?.map((id) => ({
          asset_id: id,
          storage_object_id: `storage-${id}`,
          download_url: `https://example.com/${id}`,
          method: 'GET',
          headers: {},
          expires_in_seconds: 900,
        })) ?? [];

      return new Response(
        JSON.stringify({ items, missing_asset_ids: [], unsupported_asset_ids: [] }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      );
    });

    const result = await getAssetThumbnailUrls(ids);

    expect(result.items).toHaveLength(201);
    const calls = (global.fetch as unknown as Mock).mock.calls;
    expect(calls).toHaveLength(2);
    const firstPayload = JSON.parse(String(calls[0]?.[1]?.body ?? '{}')) as {
      asset_ids?: string[];
    };
    const secondPayload = JSON.parse(String(calls[1]?.[1]?.body ?? '{}')) as {
      asset_ids?: string[];
    };
    expect(firstPayload.asset_ids).toHaveLength(200);
    expect(secondPayload.asset_ids).toHaveLength(1);
  });
});
