import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import { updateConversationMemory } from '@/lib/server/services/conversations';
import type { ConversationMemoryConfigRequest } from '@/lib/api/client/types.gen';

interface RouteContext {
  params: Promise<{
    conversationId?: string;
  }>;
}

async function extractConversationId(context: RouteContext): Promise<string | undefined> {
  const { conversationId } = await context.params;
  return conversationId;
}

function resolveErrorStatus(message: string): number {
  const normalized = message.toLowerCase();
  if (normalized.includes('missing access token')) {
    return 401;
  }
  if (normalized.includes('not found')) {
    return 404;
  }
  if (normalized.includes('validation')) {
    return 422;
  }
  return 500;
}

export async function PATCH(request: NextRequest, context: RouteContext) {
  const conversationId = await extractConversationId(context);
  if (!conversationId) {
    return NextResponse.json({ message: 'Conversation id is required.' }, { status: 400 });
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ message: 'Request body must be valid JSON.' }, { status: 400 });
  }

  if (!body || typeof body !== 'object') {
    return NextResponse.json({ message: 'Request body must be an object.' }, { status: 400 });
  }

  try {
    const updated = await updateConversationMemory(
      conversationId,
      body as ConversationMemoryConfigRequest,
    );
    return NextResponse.json(updated, { status: 200 });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to update conversation memory.';
    const status = resolveErrorStatus(message);
    return NextResponse.json({ message }, { status });
  }
}
