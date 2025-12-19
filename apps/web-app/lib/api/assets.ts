import type {
  AssetDownloadResponse,
  AssetListResponse,
  AssetResponse,
} from '@/lib/api/client/types.gen';
import { USE_API_MOCK } from '@/lib/config';
import { apiV1Path } from '@/lib/apiPaths';

function buildError(response: Response, fallback: string): Error {
  return new Error(fallback || `Request failed with ${response.status}`);
}

async function parseJson<T>(response: Response, fallback: string): Promise<T> {
  try {
    return (await response.json()) as T;
  } catch {
    throw new Error(fallback);
  }
}

export type AssetListParams = {
  limit?: number;
  offset?: number;
  assetType?: 'image' | 'file' | null;
  sourceTool?: 'image_generation' | 'code_interpreter' | 'user_upload' | 'unknown' | null;
  conversationId?: string | null;
  messageId?: number | null;
  agentKey?: string | null;
  mimeTypePrefix?: string | null;
  createdAfter?: string | null;
  createdBefore?: string | null;
};

export async function listAssets(params?: AssetListParams): Promise<AssetListResponse> {
  if (USE_API_MOCK) {
    return { items: [], next_offset: null };
  }

  const query = new URLSearchParams();
  if (params?.limit) query.set('limit', String(params.limit));
  if (params?.offset !== undefined) query.set('offset', String(params.offset));
  if (params?.assetType) query.set('asset_type', params.assetType);
  if (params?.sourceTool) query.set('source_tool', params.sourceTool);
  if (params?.conversationId) query.set('conversation_id', params.conversationId);
  if (params?.messageId !== undefined && params?.messageId !== null) {
    query.set('message_id', String(params.messageId));
  }
  if (params?.agentKey) query.set('agent_key', params.agentKey);
  if (params?.mimeTypePrefix) query.set('mime_type_prefix', params.mimeTypePrefix);
  if (params?.createdAfter) query.set('created_after', params.createdAfter);
  if (params?.createdBefore) query.set('created_before', params.createdBefore);

  const res = await fetch(apiV1Path(`/assets${query.size ? `?${query.toString()}` : ''}`), {
    cache: 'no-store',
  });

  if (!res.ok) throw buildError(res, 'Failed to load assets');
  return parseJson<AssetListResponse>(res, 'Failed to parse assets response');
}

export async function getAsset(assetId: string): Promise<AssetResponse> {
  if (USE_API_MOCK) {
    throw new Error('Asset mock not configured');
  }

  const res = await fetch(apiV1Path(`/assets/${encodeURIComponent(assetId)}`), {
    cache: 'no-store',
  });

  if (!res.ok) throw buildError(res, 'Failed to load asset');
  return parseJson<AssetResponse>(res, 'Failed to parse asset response');
}

export async function getAssetDownloadUrl(assetId: string): Promise<AssetDownloadResponse> {
  if (USE_API_MOCK) {
    throw new Error('Asset mock not configured');
  }

  const res = await fetch(
    apiV1Path(`/assets/${encodeURIComponent(assetId)}/download-url`),
    { cache: 'no-store' },
  );

  const body = await res.clone().text().catch(() => '');
  if (!res.ok) {
    let parsed: { message?: string } = {};
    if (body) {
      try {
        parsed = JSON.parse(body) as { message?: string };
      } catch {
        parsed = {};
      }
    }
    const message = parsed.message || `Failed to fetch download URL (HTTP ${res.status})`;
    throw new Error(message);
  }

  if (!body) {
    throw new Error('Empty download URL response.');
  }

  try {
    return JSON.parse(body) as AssetDownloadResponse;
  } catch {
    throw new Error('Failed to parse download URL response.');
  }
}

export async function deleteAsset(assetId: string) {
  if (USE_API_MOCK) return;

  const res = await fetch(apiV1Path(`/assets/${encodeURIComponent(assetId)}`), {
    method: 'DELETE',
  });
  if (!res.ok) throw buildError(res, 'Failed to delete asset');
}
