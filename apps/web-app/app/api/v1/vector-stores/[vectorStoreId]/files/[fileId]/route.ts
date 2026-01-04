import { NextResponse } from 'next/server';

import {
  deleteVectorStoreFile,
  getVectorStoreFile,
  VectorStoreServiceError,
} from '@/lib/server/services/vectorStores';

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ vectorStoreId: string; fileId: string }> },
) {
  const { vectorStoreId, fileId } = await params;
  try {
    const res = await getVectorStoreFile(vectorStoreId, fileId);
    return NextResponse.json(res);
  } catch (error) {
    if (error instanceof VectorStoreServiceError) {
      return NextResponse.json({ message: error.message }, { status: error.status });
    }
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
    await deleteVectorStoreFile(vectorStoreId, fileId);
    return NextResponse.json({ success: true });
  } catch (error) {
    if (error instanceof VectorStoreServiceError) {
      return NextResponse.json({ message: error.message }, { status: error.status });
    }
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
