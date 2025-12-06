import { NextResponse } from 'next/server';

import { createPresignedUploadApiV1StorageObjectsUploadUrlPost } from '@/lib/api/client/sdk.gen';
import type { StoragePresignUploadRequest } from '@/lib/api/client/types.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

export async function POST(request: Request) {
  try {
    const payload = (await request.json()) as StoragePresignUploadRequest;
    const { client, auth } = await getServerApiClient();
    const response = await createPresignedUploadApiV1StorageObjectsUploadUrlPost({
      client,
      auth,
      throwOnError: true,
      responseStyle: 'fields',
      body: payload,
    });

    if (!response.data) {
      return NextResponse.json({ message: 'Presign response missing data' }, { status: 500 });
    }

    return NextResponse.json(response.data);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to presign upload';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
