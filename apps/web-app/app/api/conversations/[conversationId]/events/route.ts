import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import { getConversationEvents } from '@/lib/server/services/conversations';

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
    return NextResponse.json({ success: false, error: 'Conversation id is required.' }, { status: 400 });
  }

  const { searchParams } = new URL(request.url);
  const modeParam = searchParams.get('mode');
  const workflowRunId = searchParams.get('workflow_run_id');

  const mode = modeParam === 'full' ? 'full' : 'transcript';

  try {
    const events = await getConversationEvents(conversationId, {
      mode,
      workflowRunId: workflowRunId || undefined,
    });

    return NextResponse.json({ success: true, data: events }, { status: 200 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load conversation events.';
    const status = resolveErrorStatus(message);
    return NextResponse.json({ success: false, error: message }, { status });
  }
}

