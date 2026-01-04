import { NextResponse } from 'next/server';

import { listStorageObjects } from '@/lib/server/services/storage';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);

  try {
    const response = await listStorageObjects({
      limit: searchParams.get('limit') ? Number(searchParams.get('limit')) : undefined,
      offset: searchParams.get('offset') ? Number(searchParams.get('offset')) : undefined,
      conversationId: searchParams.get('conversation_id'),
    });

    return NextResponse.json(response ?? { items: [], next_offset: null });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load storage objects';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
