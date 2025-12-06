import { NextResponse } from 'next/server';

import {
  attachFileApiV1VectorStoresVectorStoreIdFilesPost,
  listFilesApiV1VectorStoresVectorStoreIdFilesGet,
} from '@/lib/api/client/sdk.gen';
import type { VectorStoreFileCreateRequest } from '@/lib/api/client/types.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

export async function GET(_req: Request, { params }: { params: Promise<{ vectorStoreId: string }> }) {
  const { vectorStoreId } = await params;
  try {
    const { client, auth } = await getServerApiClient();
    const res = await listFilesApiV1VectorStoresVectorStoreIdFilesGet({
      client,
      auth,
      throwOnError: true,
      responseStyle: 'fields',
      path: { vector_store_id: vectorStoreId },
    });
    return NextResponse.json(res.data ?? { items: [], total: 0 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to list vector store files';
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

export async function POST(
  request: Request,
  { params }: { params: Promise<{ vectorStoreId: string }> },
) {
  const { vectorStoreId } = await params;
  try {
    const payload = (await request.json()) as VectorStoreFileCreateRequest;
    const { client, auth } = await getServerApiClient();
    const res = await attachFileApiV1VectorStoresVectorStoreIdFilesPost({
      client,
      auth,
      throwOnError: true,
      responseStyle: 'fields',
      path: { vector_store_id: vectorStoreId },
      body: payload,
    });
    if (!res.data) return NextResponse.json({ message: 'Attach file missing data' }, { status: 500 });
    return NextResponse.json(res.data);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to attach file';
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
