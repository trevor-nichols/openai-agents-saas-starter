import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import { deleteConversation, getConversationHistory } from '@/lib/server/services/conversations';

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
  return 500;
}

export async function GET(_request: NextRequest, context: RouteContext) {
  const conversationId = await extractConversationId(context);
  if (!conversationId) {
    return NextResponse.json({ message: 'Conversation id is required.' }, { status: 400 });
  }

  try {
    const history = await getConversationHistory(conversationId);
    return NextResponse.json(history, { status: 200 });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to load conversation history.';
    const status = resolveErrorStatus(message);
    return NextResponse.json({ message }, { status });
  }
}

export async function DELETE(_request: NextRequest, context: RouteContext) {
  const conversationId = await extractConversationId(context);
  if (!conversationId) {
    return NextResponse.json({ message: 'Conversation id is required.' }, { status: 400 });
  }

  try {
    await deleteConversation(conversationId);
    return new Response(null, { status: 204 });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to delete conversation.';
    const status = resolveErrorStatus(message);
    return NextResponse.json({ message }, { status });
  }
}
