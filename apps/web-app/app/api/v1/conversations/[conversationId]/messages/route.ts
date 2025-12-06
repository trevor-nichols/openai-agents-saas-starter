import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import { getConversationMessagesPage } from '@/lib/server/services/conversations';

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

export async function GET(request: NextRequest, context: RouteContext) {
  const conversationId = await extractConversationId(context);
  if (!conversationId) {
    return NextResponse.json({ message: 'Conversation id is required.' }, { status: 400 });
  }

  const { searchParams } = new URL(request.url);
  const cursor = searchParams.get('cursor');
  const limit = searchParams.get('limit');
  const direction = searchParams.get('direction');

  try {
    const page = await getConversationMessagesPage(conversationId, {
      cursor: cursor ?? undefined,
      limit: limit ? Number(limit) : undefined,
      direction: direction === 'asc' || direction === 'desc' ? direction : undefined,
    });

    return NextResponse.json(page, { status: 200 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load conversation messages.';
    const status = resolveErrorStatus(message);
    return NextResponse.json({ message }, { status });
  }
}
