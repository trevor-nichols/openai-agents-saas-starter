import { NextResponse } from 'next/server';

import { listConversationsAction } from '@/app/(app)/(workspace)/chat/actions';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const limit = searchParams.get('limit');
  const cursor = searchParams.get('cursor');
  const agent = searchParams.get('agent');

  const result = await listConversationsAction({
    limit: limit ? Number(limit) : undefined,
    cursor: cursor || null,
    agent: agent || null,
  });

  const status = result.success ? 200 : 500;
  if (!result.success) {
    return NextResponse.json({ error: result.error ?? 'Failed to fetch conversations' }, { status });
  }

  return NextResponse.json(
    {
      items: result.items ?? [],
      next_cursor: result.next_cursor ?? null,
    },
    { status },
  );
}
