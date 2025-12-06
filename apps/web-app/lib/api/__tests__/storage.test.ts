import { afterEach, describe, expect, it, vi } from 'vitest';

import { getAttachmentDownloadUrl } from '@/lib/api/storage';
import { apiV1Path } from '@/lib/apiPaths';

const originalFetch = global.fetch;

describe('storage API helpers', () => {
  afterEach(() => {
    if (originalFetch) {
      global.fetch = originalFetch;
    } else {
      // @ts-expect-error - cleaning up mocked fetch reference
      delete global.fetch;
    }
    vi.resetAllMocks();
  });

  it('returns presigned download payload on success', async () => {
    const payload = {
      object_id: 'obj-1',
      download_url: 'https://example.com/presign',
      method: 'GET',
      headers: {},
      bucket: 'bkt',
      object_key: 'path/file',
      expires_in_seconds: 300,
    };

    const response = new Response(JSON.stringify(payload), { status: 200 });
    global.fetch = vi.fn().mockResolvedValue(response);

    const result = await getAttachmentDownloadUrl('obj-1');
    expect(global.fetch).toHaveBeenCalledWith(apiV1Path('/storage/objects/obj-1/download-url'), {
      method: 'GET',
      cache: 'no-store',
    });
    expect(result).toEqual(payload);
  });

  it('throws when backend returns error status', async () => {
    const response = new Response(JSON.stringify({ message: 'forbidden' }), { status: 403 });
    global.fetch = vi.fn().mockResolvedValue(response);

    await expect(getAttachmentDownloadUrl('obj-1')).rejects.toThrow('forbidden');
  });

  it('throws fallback message when backend returns non-JSON error', async () => {
    const response = new Response('<html>Unavailable</html>', { status: 503 });
    global.fetch = vi.fn().mockResolvedValue(response);

    await expect(getAttachmentDownloadUrl('obj-1')).rejects.toThrow('Failed to fetch download URL (HTTP 503)');
  });
});
