import { NextResponse } from 'next/server';

import { uploadAndAttachFileApiV1VectorStoresVectorStoreIdFilesUploadPost } from '@/lib/api/client/sdk.gen';
import type { VectorStoreFileUploadRequest } from '@/lib/api/client/types.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

export async function POST(
  request: Request,
  { params }: { params: Promise<{ vectorStoreId: string }> },
) {
  const { vectorStoreId } = await params;

  try {
    const payload = (await request.json()) as VectorStoreFileUploadRequest;
    const { client, auth } = await getServerApiClient();
    const res = await uploadAndAttachFileApiV1VectorStoresVectorStoreIdFilesUploadPost({
      client,
      auth,
      throwOnError: false,
      responseStyle: 'fields',
      path: { vector_store_id: vectorStoreId },
      body: payload,
    });

    const status = res.response?.status ?? (res.error ? 500 : 201);
    if (res.error || status >= 400) {
      const err = res.error;
      const detail =
        typeof err === 'string'
          ? err
          : err && typeof err === 'object' && 'detail' in err && typeof (err as any).detail === 'string'
            ? (err as any).detail
            : undefined;
      const message =
        typeof err === 'string'
          ? err
          : err && typeof err === 'object' && 'message' in err && typeof (err as any).message === 'string'
            ? (err as any).message
            : detail ?? 'Failed to upload vector store file';
      return NextResponse.json({ message, detail }, { status });
    }

    if (!res.data) {
      return NextResponse.json({ message: 'Vector store upload missing data' }, { status: 500 });
    }
    return NextResponse.json(res.data, { status });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to upload vector store file';
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
