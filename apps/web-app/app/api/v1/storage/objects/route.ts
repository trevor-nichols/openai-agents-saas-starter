import { NextResponse } from 'next/server';

import { listObjectsApiV1StorageObjectsGet } from '@/lib/api/client/sdk.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);

  try {
    const { client, auth } = await getServerApiClient();
    const response = await listObjectsApiV1StorageObjectsGet({
      client,
      auth,
      responseStyle: 'fields',
      throwOnError: true,
      query: {
        limit: searchParams.get('limit') ? Number(searchParams.get('limit')) : undefined,
        offset: searchParams.get('offset') ? Number(searchParams.get('offset')) : undefined,
        conversation_id: searchParams.get('conversation_id') ?? undefined,
      },
    });

    return NextResponse.json(response.data ?? { items: [], next_offset: null });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load storage objects';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
