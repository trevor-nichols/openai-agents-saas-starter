import { NextResponse } from 'next/server';

import { getPresignedDownloadUrl } from '@/lib/server/services/storage';

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ objectId: string }> },
) {
  const { objectId } = await params;

  try {
    const response = await getPresignedDownloadUrl(objectId);
    return NextResponse.json(response);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to fetch download URL';
    const status =
      typeof message === 'string' && message.toLowerCase().includes('missing access token')
        ? 401
        : 500;

    return NextResponse.json({ message }, { status });
  }
}
