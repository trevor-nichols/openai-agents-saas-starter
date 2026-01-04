import { NextResponse } from 'next/server';

import type { VectorStoreCreateRequest } from '@/lib/api/client/types.gen';
import { createVectorStore, listVectorStores, VectorStoreServiceError } from '@/lib/server/services/vectorStores';

export async function GET() {
  try {
    const res = await listVectorStores();
    return NextResponse.json(res ?? { items: [], total: 0 });
  } catch (error) {
    if (error instanceof VectorStoreServiceError) {
      return NextResponse.json({ message: error.message }, { status: error.status });
    }
    const message = error instanceof Error ? error.message : 'Failed to load vector stores';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}

export async function POST(request: Request) {
  try {
    const payload = (await request.json()) as VectorStoreCreateRequest;
    const res = await createVectorStore(payload);
    return NextResponse.json(res);
  } catch (error) {
    if (error instanceof VectorStoreServiceError) {
      return NextResponse.json({ message: error.message }, { status: error.status });
    }
    const message = error instanceof Error ? error.message : 'Failed to create vector store';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
