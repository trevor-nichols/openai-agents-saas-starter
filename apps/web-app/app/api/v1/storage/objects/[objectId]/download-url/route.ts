import { NextResponse } from 'next/server';

import { getDownloadUrlApiV1StorageObjectsObjectIdDownloadUrlGet } from '@/lib/api/client/sdk.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ objectId: string }> },
) {
  const { objectId } = await params;

  try {
    const { client, auth } = await getServerApiClient();
    const response = await getDownloadUrlApiV1StorageObjectsObjectIdDownloadUrlGet({
      client,
      auth,
      throwOnError: true,
      responseStyle: 'fields',
      path: { object_id: objectId },
    });

    if (!response.data) {
      return NextResponse.json({ message: 'Download URL missing data' }, { status: 500 });
    }

    return NextResponse.json(response.data);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to fetch download URL';
    const status =
      typeof message === 'string' && message.toLowerCase().includes('missing access token')
        ? 401
        : 500;

    return NextResponse.json({ message }, { status });
  }
}
