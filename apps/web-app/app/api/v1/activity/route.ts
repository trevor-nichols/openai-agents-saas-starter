import { NextResponse } from 'next/server';

import { listActivityEventsApiV1ActivityGet } from '@/lib/api/client/sdk.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);

  try {
    const { client, auth } = await getServerApiClient();

    const response = await listActivityEventsApiV1ActivityGet({
      client,
      auth,
      responseStyle: 'fields',
      throwOnError: true,
      query: {
        limit: searchParams.get('limit') ? Number(searchParams.get('limit')) : undefined,
        cursor: searchParams.get('cursor') ?? undefined,
        action: searchParams.get('action') ?? undefined,
        actor_id: searchParams.get('actor_id') ?? undefined,
        object_type: searchParams.get('object_type') ?? undefined,
        object_id: searchParams.get('object_id') ?? undefined,
        status: searchParams.get('status') ?? undefined,
        request_id: searchParams.get('request_id') ?? undefined,
        created_after: searchParams.get('created_after') ?? undefined,
        created_before: searchParams.get('created_before') ?? undefined,
      },
    });

    return NextResponse.json(response.data ?? { items: [], next_cursor: null });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load activity events';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
