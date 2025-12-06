import { NextRequest, NextResponse } from 'next/server';

import type { AgentChatRequest } from '@/lib/api/client/types.gen';
import { sendChatMessage } from '@/lib/server/services/chat';

export async function POST(request: NextRequest) {
  const payload = (await request.json()) as AgentChatRequest;

  try {
    const response = await sendChatMessage(payload);
    return NextResponse.json(response, { status: 200 });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to send chat message.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 502;
    return NextResponse.json({ message }, { status });
  }
}

