import { NextResponse } from 'next/server';

import { getAssetThumbnailUrls } from '@/lib/server/services/assets';

function parseAssetIds(payload: unknown): string[] | { error: string } {
  if (!payload || typeof payload !== 'object') {
    return { error: 'Invalid request body' };
  }
  const assetIds = (payload as { asset_ids?: unknown }).asset_ids;
  if (!Array.isArray(assetIds)) {
    return { error: 'asset_ids must be an array' };
  }
  const normalized = assetIds.filter((value): value is string => typeof value === 'string');
  if (normalized.length !== assetIds.length) {
    return { error: 'asset_ids must contain only strings' };
  }
  if (normalized.length === 0) {
    return { error: 'asset_ids must not be empty' };
  }
  if (normalized.length > 200) {
    return { error: 'asset_ids must contain 200 items or fewer' };
  }
  return normalized;
}

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ message: 'Invalid JSON body' }, { status: 400 });
  }

  const assetIds = parseAssetIds(body);
  if (!Array.isArray(assetIds)) {
    return NextResponse.json({ message: assetIds.error }, { status: 400 });
  }

  try {
    const response = await getAssetThumbnailUrls(assetIds);
    return NextResponse.json(response);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to load asset thumbnails';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
