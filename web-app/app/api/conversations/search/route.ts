import { NextResponse } from 'next/server';

import { searchConversationsAction } from '@/app/(app)/(workspace)/chat/actions';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.get('q');
  if (!query) {
    return NextResponse.json({ error: 'Query is required' }, { status: 400 });
  }
  const limit = searchParams.get('limit');
  const cursor = searchParams.get('cursor');
  const agent = searchParams.get('agent');

  const result = await searchConversationsAction({
    query,
    limit: limit ? Number(limit) : undefined,
    cursor: cursor || null,
    agent: agent || null,
  });

  const status = result.success ? 200 : 500;
  if (!result.success) {
    return NextResponse.json({ error: result.error ?? 'Failed to search conversations' }, { status });
  }

  return NextResponse.json(
    {
      items: result.items ?? [],
      next_cursor: result.next_cursor ?? null,
    },
    { status },
  );
}
