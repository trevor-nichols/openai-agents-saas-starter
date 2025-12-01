import { NextResponse } from 'next/server';

import { createVectorStoreApiV1VectorStoresPost } from '@/lib/api/client/sdk.gen';
import type { VectorStoreCreateRequest } from '@/lib/api/client/types.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

export async function POST(request: Request) {
  try {
    const payload = (await request.json()) as VectorStoreCreateRequest;
    const { client, auth } = await getServerApiClient();
    const res = await createVectorStoreApiV1VectorStoresPost({
      client,
      auth,
      throwOnError: true,
      responseStyle: 'fields',
      body: payload,
    });
    if (!res.data) return NextResponse.json({ message: 'Vector store create missing data' }, { status: 500 });
    return NextResponse.json(res.data);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to create vector store';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
