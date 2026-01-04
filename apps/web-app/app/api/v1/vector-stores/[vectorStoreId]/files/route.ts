import { NextResponse } from 'next/server';

import type { VectorStoreFileCreateRequest } from '@/lib/api/client/types.gen';
import {
  attachVectorStoreFile,
  listVectorStoreFiles,
  VectorStoreServiceError,
} from '@/lib/server/services/vectorStores';

export async function GET(_req: Request, { params }: { params: Promise<{ vectorStoreId: string }> }) {
  const { vectorStoreId } = await params;
  try {
    const res = await listVectorStoreFiles(vectorStoreId);
    return NextResponse.json(res ?? { items: [], total: 0 });
  } catch (error) {
    if (error instanceof VectorStoreServiceError) {
      return NextResponse.json({ message: error.message }, { status: error.status });
    }
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
    const res = await attachVectorStoreFile(vectorStoreId, payload);
    return NextResponse.json(res);
  } catch (error) {
    if (error instanceof VectorStoreServiceError) {
      return NextResponse.json({ message: error.message }, { status: error.status });
    }
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
