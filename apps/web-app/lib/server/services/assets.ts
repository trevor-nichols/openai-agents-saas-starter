'use server';

import {
  deleteAssetApiV1AssetsAssetIdDelete,
  getAssetApiV1AssetsAssetIdGet,
  getAssetDownloadUrlApiV1AssetsAssetIdDownloadUrlGet,
  listAssetsApiV1AssetsGet,
} from '@/lib/api/client/sdk.gen';
import type {
  AssetDownloadResponse,
  AssetListResponse,
  AssetResponse,
} from '@/lib/api/client/types.gen';

import { getServerApiClient } from '../apiClient';

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
  const { client, auth } = await getServerApiClient();

  const response = await listAssetsApiV1AssetsGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    query: {
      limit: params?.limit,
      offset: params?.offset,
      asset_type: params?.assetType ?? undefined,
      source_tool: params?.sourceTool ?? undefined,
      conversation_id: params?.conversationId ?? undefined,
      message_id: params?.messageId ?? undefined,
      agent_key: params?.agentKey ?? undefined,
      mime_type_prefix: params?.mimeTypePrefix ?? undefined,
      created_after: params?.createdAfter ?? undefined,
      created_before: params?.createdBefore ?? undefined,
    },
  });

  return response.data ?? { items: [], next_offset: null };
}

export async function getAsset(assetId: string): Promise<AssetResponse> {
  if (!assetId) {
    throw new Error('Asset id is required.');
  }

  const { client, auth } = await getServerApiClient();
  const response = await getAssetApiV1AssetsAssetIdGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    path: { asset_id: assetId },
  });

  const payload = response.data;
  if (!payload) {
    throw new Error('Asset not found.');
  }

  return payload;
}

export async function getAssetDownloadUrl(assetId: string): Promise<AssetDownloadResponse> {
  if (!assetId) {
    throw new Error('Asset id is required.');
  }

  const { client, auth } = await getServerApiClient();
  const response = await getAssetDownloadUrlApiV1AssetsAssetIdDownloadUrlGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    path: { asset_id: assetId },
  });

  const payload = response.data;
  if (!payload) {
    throw new Error('Download URL payload missing.');
  }

  return payload;
}

export async function deleteAsset(assetId: string): Promise<void> {
  if (!assetId) {
    throw new Error('Asset id is required.');
  }

  const { client, auth } = await getServerApiClient();
  await deleteAssetApiV1AssetsAssetIdDelete({
    client,
    auth,
    throwOnError: true,
    path: { asset_id: assetId },
  });
}
