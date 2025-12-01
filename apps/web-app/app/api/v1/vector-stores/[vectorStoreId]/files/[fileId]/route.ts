import { NextResponse } from 'next/server';

import {
  deleteFileApiV1VectorStoresVectorStoreIdFilesFileIdDelete,
  getFileApiV1VectorStoresVectorStoreIdFilesFileIdGet,
} from '@/lib/api/client/sdk.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ vectorStoreId: string; fileId: string }> },
) {
  const { vectorStoreId, fileId } = await params;
  try {
    const { client, auth } = await getServerApiClient();
    const res = await getFileApiV1VectorStoresVectorStoreIdFilesFileIdGet({
      client,
      auth,
      throwOnError: true,
      responseStyle: 'fields',
      path: { vector_store_id: vectorStoreId, file_id: fileId },
    });

    if (!res.data) {
      return NextResponse.json({ message: 'Vector store file not found' }, { status: 404 });
    }

    return NextResponse.json(res.data);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load vector store file';
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

export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ vectorStoreId: string; fileId: string }> },
) {
  const { vectorStoreId, fileId } = await params;
  try {
    const { client, auth } = await getServerApiClient();
    await deleteFileApiV1VectorStoresVectorStoreIdFilesFileIdDelete({
      client,
      auth,
      throwOnError: true,
      path: { vector_store_id: vectorStoreId, file_id: fileId },
    });
    return NextResponse.json({ success: true });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to delete vector store file';
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
