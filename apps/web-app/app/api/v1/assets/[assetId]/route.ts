import { NextResponse } from 'next/server';

import { deleteAsset, getAsset } from '@/lib/server/services/assets';

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ assetId: string }> },
) {
  const { assetId } = await params;

  try {
    const asset = await getAsset(assetId);
    return NextResponse.json(asset);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load asset';
    const normalized = message.toLowerCase();
    const status = normalized.includes('missing access token')
      ? 401
      : normalized.includes('not found')
        ? 404
        : 500;
    return NextResponse.json({ message }, { status });
  }
}

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ assetId: string }> },
) {
  const { assetId } = await params;

  try {
    await deleteAsset(assetId);
    return NextResponse.json({ success: true });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to delete asset';
    const normalized = message.toLowerCase();
    const status = normalized.includes('missing access token')
      ? 401
      : normalized.includes('not found')
        ? 404
        : 500;
    return NextResponse.json({ message }, { status });
  }
}
