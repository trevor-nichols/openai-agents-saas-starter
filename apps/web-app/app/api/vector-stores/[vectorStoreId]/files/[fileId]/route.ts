import { NextResponse } from 'next/server';

import { deleteFileApiV1VectorStoresVectorStoreIdFilesFileIdDelete } from '@/lib/api/client/sdk.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

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
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
