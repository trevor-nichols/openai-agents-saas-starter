import { NextResponse } from 'next/server';

import {
  bindAgentToVectorStoreApiV1VectorStoresVectorStoreIdBindingsAgentKeyPost,
  unbindAgentFromVectorStoreApiV1VectorStoresVectorStoreIdBindingsAgentKeyDelete,
} from '@/lib/api/client/sdk.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

export async function POST(
  _req: Request,
  { params }: { params: Promise<{ vectorStoreId: string; agentKey: string }> },
) {
  const { vectorStoreId, agentKey } = await params;

  try {
    const { client, auth } = await getServerApiClient();
    await bindAgentToVectorStoreApiV1VectorStoresVectorStoreIdBindingsAgentKeyPost({
      client,
      auth,
      throwOnError: true,
      responseStyle: 'fields',
      path: { vector_store_id: vectorStoreId, agent_key: agentKey },
    });

    return NextResponse.json({ success: true });
  } catch (error) {
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
    const { client, auth } = await getServerApiClient();
    await unbindAgentFromVectorStoreApiV1VectorStoresVectorStoreIdBindingsAgentKeyDelete({
      client,
      auth,
      throwOnError: true,
      path: { vector_store_id: vectorStoreId, agent_key: agentKey },
    });

    return NextResponse.json({ success: true });
  } catch (error) {
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
