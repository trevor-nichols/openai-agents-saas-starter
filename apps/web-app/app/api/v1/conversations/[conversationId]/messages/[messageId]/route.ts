import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import { deleteConversationMessage } from '@/lib/server/services/conversations';

interface RouteContext {
  params: Promise<{
    conversationId?: string;
    messageId?: string;
  }>;
}

async function extractParams(
  context: RouteContext,
): Promise<{ conversationId?: string; messageId?: string }> {
  const { conversationId, messageId } = await context.params;
  return { conversationId, messageId };
}

function resolveErrorStatus(message: string): number {
  const normalized = message.toLowerCase();
  if (normalized.includes('missing access token') || normalized.includes('missing credentials')) {
    return 401;
  }
  if (normalized.includes('not found')) {
    return 404;
  }
  return 500;
}

export async function DELETE(_request: NextRequest, context: RouteContext) {
  const { conversationId, messageId } = await extractParams(context);
  if (!conversationId) {
    return NextResponse.json({ message: 'Conversation id is required.' }, { status: 400 });
  }
  if (!messageId) {
    return NextResponse.json({ message: 'Message id is required.' }, { status: 400 });
  }

  try {
    const result = await deleteConversationMessage({ conversationId, messageId });
    return NextResponse.json(result, { status: 200 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to delete message.';
    const status = resolveErrorStatus(message);
    return NextResponse.json({ message }, { status });
  }
}

