import { NextResponse } from 'next/server';

import { listConversationsPage } from '@/lib/server/services/conversations';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const limit = searchParams.get('limit');
  const cursor = searchParams.get('cursor');
  const agent = searchParams.get('agent');

  try {
    const page = await listConversationsPage({
      limit: limit ? Number(limit) : undefined,
      cursor: cursor || null,
      agent: agent || null,
    });

    return NextResponse.json(
      {
        items: page.items ?? [],
        next_cursor: page.next_cursor ?? null,
      },
      { status: 200 },
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to fetch conversations';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
