import { NextResponse } from 'next/server';

import {
  attachFileApiV1VectorStoresVectorStoreIdFilesPost,
  deleteVectorStoreApiV1VectorStoresVectorStoreIdDelete,
  listFilesApiV1VectorStoresVectorStoreIdFilesGet,
  searchVectorStoreApiV1VectorStoresVectorStoreIdSearchPost,
} from '@/lib/api/client/sdk.gen';
import type { VectorStoreFileCreateRequest, VectorStoreSearchRequest, VectorStoreSearchResponse } from '@/lib/api/client/types.gen';
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
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
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
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}

export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ vectorStoreId: string }> },
) {
  const { vectorStoreId } = await params;
  try {
    const { client, auth } = await getServerApiClient();
    await deleteVectorStoreApiV1VectorStoresVectorStoreIdDelete({
      client,
      auth,
      throwOnError: true,
      path: { vector_store_id: vectorStoreId },
    });
    return NextResponse.json({ success: true });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to delete vector store';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}

export async function PUT(
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
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
