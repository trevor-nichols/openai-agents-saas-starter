import { NextResponse } from 'next/server';

import { searchVectorStoreApiV1VectorStoresVectorStoreIdSearchPost } from '@/lib/api/client/sdk.gen';
import type { VectorStoreSearchRequest, VectorStoreSearchResponse } from '@/lib/api/client/types.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

function isVectorStoreSearchResponse(payload: unknown): payload is VectorStoreSearchResponse {
  if (!payload || typeof payload !== 'object') return false;
  const record = payload as Record<string, unknown>;
  return typeof record.object === 'string' && typeof record.search_query === 'string';
}

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
    if (!isVectorStoreSearchResponse(res.data)) {
      return NextResponse.json(
        { message: 'Vector store search returned an invalid payload.' },
        { status: 502 },
      );
    }
    return NextResponse.json(res.data);
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
