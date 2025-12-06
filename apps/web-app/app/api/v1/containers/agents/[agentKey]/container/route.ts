import { NextResponse } from 'next/server';

import {
  bindAgentContainerApiV1ContainersAgentsAgentKeyContainerPost,
  unbindAgentContainerApiV1ContainersAgentsAgentKeyContainerDelete,
} from '@/lib/api/client/sdk.gen';
import type { ContainerBindRequest } from '@/lib/api/client/types.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

export async function POST(
  request: Request,
  { params }: { params: Promise<{ agentKey: string }> },
) {
  const { agentKey } = await params;

  try {
    const payload = (await request.json()) as ContainerBindRequest;
    if (!payload?.container_id) {
      return NextResponse.json({ message: 'container_id is required' }, { status: 400 });
    }

    const { client, auth } = await getServerApiClient();
    await bindAgentContainerApiV1ContainersAgentsAgentKeyContainerPost({
      client,
      auth,
      throwOnError: true,
      responseStyle: 'fields',
      path: { agent_key: agentKey },
      body: payload,
    });

    return NextResponse.json({ success: true });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to bind container';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ agentKey: string }> },
) {
  const { agentKey } = await params;

  try {
    const { client, auth } = await getServerApiClient();
    await unbindAgentContainerApiV1ContainersAgentsAgentKeyContainerDelete({
      client,
      auth,
      throwOnError: true,
      path: { agent_key: agentKey },
    });

    return NextResponse.json({ success: true });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to unbind container';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
