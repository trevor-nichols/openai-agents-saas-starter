import { NextRequest, NextResponse } from 'next/server';

import { getPresignedDownloadUrl } from '@/lib/server/services/storage';

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ objectId: string }> },
) {
  try {
    const { objectId } = await params;
    const data = await getPresignedDownloadUrl(objectId);
    return NextResponse.json(data, { status: 200 });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to fetch download URL.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 502;
    return NextResponse.json({ message }, { status });
  }
}
