import { NextResponse } from 'next/server';

import type { VectorStoreFileUploadRequest } from '@/lib/api/client/types.gen';
import {
  uploadVectorStoreFile,
  VectorStoreServiceError,
} from '@/lib/server/services/vectorStores';

export async function POST(
  request: Request,
  { params }: { params: Promise<{ vectorStoreId: string }> },
) {
  const { vectorStoreId } = await params;

  try {
    const payload = (await request.json()) as VectorStoreFileUploadRequest;
    const res = await uploadVectorStoreFile(vectorStoreId, payload);
    return NextResponse.json(res.data, { status: res.status });
  } catch (error) {
    if (error instanceof VectorStoreServiceError) {
      return NextResponse.json(
        { message: error.message, detail: error.detail },
        { status: error.status },
      );
    }
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
