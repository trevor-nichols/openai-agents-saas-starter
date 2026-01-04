import { NextResponse } from 'next/server';

import type { VectorStoreSearchRequest, VectorStoreSearchResponse } from '@/lib/api/client/types.gen';
import { searchVectorStore, VectorStoreServiceError } from '@/lib/server/services/vectorStores';

export async function POST(
  request: Request,
  { params }: { params: Promise<{ vectorStoreId: string }> },
) {
  const { vectorStoreId } = await params;
  try {
    const payload = (await request.json()) as VectorStoreSearchRequest;
    const res = await searchVectorStore(vectorStoreId, payload);
    return NextResponse.json(res as VectorStoreSearchResponse);
  } catch (error) {
    if (error instanceof VectorStoreServiceError) {
      return NextResponse.json({ message: error.message }, { status: error.status });
    }
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
