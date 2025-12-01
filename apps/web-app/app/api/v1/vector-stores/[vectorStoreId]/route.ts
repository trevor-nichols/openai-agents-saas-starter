import { NextResponse } from 'next/server';

import {
  deleteVectorStoreApiV1VectorStoresVectorStoreIdDelete,
  getVectorStoreApiV1VectorStoresVectorStoreIdGet,
} from '@/lib/api/client/sdk.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

export async function GET(_req: Request, { params }: { params: Promise<{ vectorStoreId: string }> }) {
  const { vectorStoreId } = await params;
  try {
    const { client, auth } = await getServerApiClient();
    const res = await getVectorStoreApiV1VectorStoresVectorStoreIdGet({
      client,
      auth,
      throwOnError: true,
      responseStyle: 'fields',
      path: { vector_store_id: vectorStoreId },
    });

    if (!res.data) {
      return NextResponse.json({ message: 'Vector store not found' }, { status: 404 });
    }

    return NextResponse.json(res.data);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load vector store';
    const normalized = message.toLowerCase();
    if (normalized.includes('missing access token')) {
      return NextResponse.json({ message }, { status: 401 });
    }
    if (normalized.includes('not found')) {
      return NextResponse.json({ message }, { status: 404 });
    }
    const status = 500;
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
