import { NextResponse } from 'next/server';

import { getAssetDownloadUrl } from '@/lib/server/services/assets';

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ assetId: string }> },
) {
  const { assetId } = await params;

  try {
    const payload = await getAssetDownloadUrl(assetId);
    return NextResponse.json(payload);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to fetch download URL';
    const normalized = message.toLowerCase();
    const status = normalized.includes('missing access token')
      ? 401
      : normalized.includes('not found')
        ? 404
        : 500;
    return NextResponse.json({ message }, { status });
  }
}
