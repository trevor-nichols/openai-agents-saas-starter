import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import { getAgentStatus } from '@/lib/server/services/agents';

interface RouteContext {
  params: Promise<{
    agentName: string;
  }>;
}

function resolveErrorStatus(message: string): number {
  const normalized = message.toLowerCase();
  if (normalized.includes('missing access token')) {
    return 401;
  }
  if (normalized.includes('not found')) {
    return 404;
  }
  return 500;
}

export async function GET(_request: NextRequest, context: RouteContext) {
  const { agentName } = await context.params;
  if (!agentName) {
    return NextResponse.json({ message: 'Agent name is required.' }, { status: 400 });
  }

  try {
    const statusPayload = await getAgentStatus(agentName);
    return NextResponse.json(statusPayload, { status: 200 });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to load agent status.';
    const status = resolveErrorStatus(message);
    return NextResponse.json({ message }, { status });
  }
}
