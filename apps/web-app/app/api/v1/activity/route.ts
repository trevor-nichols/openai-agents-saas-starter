import { NextResponse } from 'next/server';

import { listActivityEvents } from '@/lib/server/services/activity';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);

  try {
    const payload = await listActivityEvents({
      limit: searchParams.get('limit') ? Number(searchParams.get('limit')) : undefined,
      cursor: searchParams.get('cursor'),
      action: searchParams.get('action'),
      actorId: searchParams.get('actor_id'),
      objectType: searchParams.get('object_type'),
      objectId: searchParams.get('object_id'),
      status: searchParams.get('status'),
      requestId: searchParams.get('request_id'),
      createdAfter: searchParams.get('created_after'),
      createdBefore: searchParams.get('created_before'),
    });

    return NextResponse.json(payload);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load activity events';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
