import { vi } from 'vitest';

import type { AssetListResponse } from '@/lib/api/client/types.gen';

import { GET } from './route';

const listAssets = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/assets', () => ({
  listAssets,
}));

describe('/api/assets route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns asset list with parsed query params', async () => {
    const payload: AssetListResponse = {
      items: [],
      next_offset: null,
    };
    listAssets.mockResolvedValueOnce(payload);

    const response = await GET(
      new Request(
        'http://localhost/api/v1/assets?limit=10&offset=20&asset_type=image&source_tool=image_generation&conversation_id=conv-1&message_id=2&agent_key=triage&mime_type_prefix=image/&created_after=2025-01-01T00:00:00Z&created_before=2025-01-02T00:00:00Z',
      ),
    );

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(payload);
    expect(listAssets).toHaveBeenCalledWith({
      limit: 10,
      offset: 20,
      assetType: 'image',
      sourceTool: 'image_generation',
      conversationId: 'conv-1',
      messageId: 2,
      agentKey: 'triage',
      mimeTypePrefix: 'image/',
      createdAfter: '2025-01-01T00:00:00Z',
      createdBefore: '2025-01-02T00:00:00Z',
    });
  });

  it('returns 400 when offset is invalid', async () => {
    const response = await GET(new Request('http://localhost/api/v1/assets?offset=abc'));

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ message: 'offset must be a non-negative integer' });
  });

  it('returns 401 when missing access token error surfaces', async () => {
    listAssets.mockRejectedValueOnce(new Error('Missing access token'));

    const response = await GET(new Request('http://localhost/api/v1/assets'));

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({ message: 'Missing access token' });
  });
});
