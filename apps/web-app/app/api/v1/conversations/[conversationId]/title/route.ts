import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import { ConversationTitleApiError, updateConversationTitle } from '@/lib/server/services/conversations';
import type { ConversationTitleUpdateRequest } from '@/lib/api/client/types.gen';

interface RouteContext {
  params: Promise<{
    conversationId?: string;
  }>;
}

async function extractConversationId(context: RouteContext): Promise<string | undefined> {
  const { conversationId } = await context.params;
  return conversationId;
}

function resolveAuthErrorStatus(error: unknown): number | null {
  if (!(error instanceof Error)) {
    return null;
  }
  const normalized = error.message.toLowerCase();
  if (normalized.includes('missing access token') || normalized.includes('missing credentials')) {
    return 401;
  }
  return null;
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
    const updated = await updateConversationTitle(
      conversationId,
      body as ConversationTitleUpdateRequest,
      { tenantRole: request.headers.get('x-tenant-role') },
    );
    return NextResponse.json(updated, { status: 200 });
  } catch (error) {
    if (error instanceof ConversationTitleApiError) {
      return NextResponse.json({ message: error.message }, { status: error.status });
    }

    const authStatus = resolveAuthErrorStatus(error);
    if (authStatus) {
      const message = error instanceof Error ? error.message : 'Missing access token';
      return NextResponse.json({ message }, { status: authStatus });
    }

    const message = error instanceof Error ? error.message : 'Failed to update conversation title.';
    return NextResponse.json({ message }, { status: 500 });
  }
}
