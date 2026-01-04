import { NextResponse } from 'next/server';

import { deleteVectorStore, getVectorStore, VectorStoreServiceError } from '@/lib/server/services/vectorStores';

export async function GET(_req: Request, { params }: { params: Promise<{ vectorStoreId: string }> }) {
  const { vectorStoreId } = await params;
  try {
    const res = await getVectorStore(vectorStoreId);
    return NextResponse.json(res);
  } catch (error) {
    if (error instanceof VectorStoreServiceError) {
      return NextResponse.json({ message: error.message }, { status: error.status });
    }
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
    await deleteVectorStore(vectorStoreId);
    return NextResponse.json({ success: true });
  } catch (error) {
    if (error instanceof VectorStoreServiceError) {
      return NextResponse.json({ message: error.message }, { status: error.status });
    }
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
