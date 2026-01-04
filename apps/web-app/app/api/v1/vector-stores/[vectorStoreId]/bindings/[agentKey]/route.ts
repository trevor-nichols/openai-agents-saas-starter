import { NextResponse } from 'next/server';

import {
  bindAgentToVectorStore,
  unbindAgentFromVectorStore,
  VectorStoreServiceError,
} from '@/lib/server/services/vectorStores';

export async function POST(
  _req: Request,
  { params }: { params: Promise<{ vectorStoreId: string; agentKey: string }> },
) {
  const { vectorStoreId, agentKey } = await params;

  try {
    await bindAgentToVectorStore(vectorStoreId, agentKey);

    return NextResponse.json({ success: true });
  } catch (error) {
    if (error instanceof VectorStoreServiceError) {
      return NextResponse.json({ message: error.message }, { status: error.status });
    }
    const message = error instanceof Error ? error.message : 'Failed to bind agent to vector store';
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
  { params }: { params: Promise<{ vectorStoreId: string; agentKey: string }> },
) {
  const { vectorStoreId, agentKey } = await params;

  try {
    await unbindAgentFromVectorStore(vectorStoreId, agentKey);

    return NextResponse.json({ success: true });
  } catch (error) {
    if (error instanceof VectorStoreServiceError) {
      return NextResponse.json({ message: error.message }, { status: error.status });
    }
    const message = error instanceof Error ? error.message : 'Failed to unbind agent from vector store';
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
