import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import { openConversationLedgerStream } from '@/lib/server/services/conversations';

type RouteContext = {
  params: Promise<{
    conversationId?: string;
  }>;
};

async function extractConversationId(context: RouteContext): Promise<string | undefined> {
  const { conversationId } = await context.params;
  return conversationId;
}

export async function GET(request: NextRequest, context: RouteContext) {
  const conversationId = await extractConversationId(context);
  if (!conversationId) {
    return NextResponse.json({ success: false, error: 'Conversation id is required.' }, { status: 400 });
  }

  const { searchParams } = new URL(request.url);
  const cursor = searchParams.get('cursor');

  try {
    return await openConversationLedgerStream({
      conversationId,
      cursor: cursor ?? undefined,
      signal: request.signal,
      tenantRole: request.headers.get('x-tenant-role'),
    });
  } catch (error) {
    const message =
      error instanceof Error
        ? error.message || String(error)
        : String(error ?? 'Failed to open conversation ledger stream.');

    const normalized = `${message} ${String(error ?? '')}`.toLowerCase();
    const status = normalized.includes('access token')
      ? 401
      : normalized.includes('not found')
        ? 404
        : 502;

    return new Response(message, { status });
  }
}

