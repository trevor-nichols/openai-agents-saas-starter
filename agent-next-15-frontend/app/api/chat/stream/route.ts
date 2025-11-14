import { NextRequest, NextResponse } from 'next/server';

import type { AgentChatRequest } from '@/lib/api/client/types.gen';
import { openChatStream } from '@/lib/server/services/chat';

export async function POST(request: NextRequest) {
  const payload = (await request.json()) as AgentChatRequest;

  try {
    return await openChatStream(payload, { signal: request.signal });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to start chat stream.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 502;
    return NextResponse.json({ message }, { status });
  }
}
