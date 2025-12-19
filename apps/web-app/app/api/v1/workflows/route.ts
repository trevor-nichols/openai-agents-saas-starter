import { NextResponse } from 'next/server';

import { listWorkflowsApiV1WorkflowsGet } from '@/lib/api/client/sdk.gen';
import { getServerApiClient } from '@/lib/server/apiClient';
import { parseOptionalLimit } from '../_utils/pagination';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);

  try {
    const parsedLimit = parseOptionalLimit(searchParams.get('limit'));
    if (!parsedLimit.ok) {
      return NextResponse.json({ message: parsedLimit.error }, { status: 400 });
    }

    const { client, auth } = await getServerApiClient();
    const response = await listWorkflowsApiV1WorkflowsGet({
      client,
      auth,
      responseStyle: 'fields',
      throwOnError: true,
      query: {
        limit: parsedLimit.value,
        cursor: searchParams.get('cursor') || undefined,
        search: searchParams.get('search') || undefined,
      },
    });

    return NextResponse.json(response.data ?? { items: [], next_cursor: null, total: 0 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load workflows';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
