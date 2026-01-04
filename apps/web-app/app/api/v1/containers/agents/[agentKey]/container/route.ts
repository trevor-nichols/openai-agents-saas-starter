import { NextResponse } from 'next/server';

import type { ContainerBindRequest } from '@/lib/api/client/types.gen';
import { bindAgentContainer, unbindAgentContainer } from '@/lib/server/services/containers';

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

    await bindAgentContainer(agentKey, payload);

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
    await unbindAgentContainer(agentKey);

    return NextResponse.json({ success: true });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to unbind container';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
