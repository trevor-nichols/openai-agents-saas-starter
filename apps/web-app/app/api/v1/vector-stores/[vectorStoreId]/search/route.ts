import { NextResponse } from 'next/server';

import { searchVectorStoreApiV1VectorStoresVectorStoreIdSearchPost } from '@/lib/api/client/sdk.gen';
import type { VectorStoreSearchRequest, VectorStoreSearchResponse } from '@/lib/api/client/types.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

export async function POST(
  request: Request,
  { params }: { params: Promise<{ vectorStoreId: string }> },
) {
  const { vectorStoreId } = await params;
  try {
    const payload = (await request.json()) as VectorStoreSearchRequest;
    const { client, auth } = await getServerApiClient();
    const res = await searchVectorStoreApiV1VectorStoresVectorStoreIdSearchPost({
      client,
      auth,
      throwOnError: true,
      responseStyle: 'fields',
      path: { vector_store_id: vectorStoreId },
      body: payload,
    });
    return NextResponse.json((res.data ?? {}) as VectorStoreSearchResponse);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to search vector store';
    const normalized = message.toLowerCase();
    if (normalized.includes('missing access token')) {
      return NextResponse.json({ message }, { status: 401 });
    }
    if (normalized.includes('not found')) {
      return NextResponse.json({ message }, { status: 404 });
    }
    return NextResponse.json({ message }, { status: 500 });
  }
}
