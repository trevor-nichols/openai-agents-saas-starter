import { NextResponse } from 'next/server';

import { listWorkflowRunsApiV1WorkflowsRunsGet } from '@/lib/api/client/sdk.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);

  try {
    const { client, auth } = await getServerApiClient();
    const response = await listWorkflowRunsApiV1WorkflowsRunsGet({
      client,
      auth,
      responseStyle: 'fields',
      throwOnError: true,
      query: {
        workflow_key: searchParams.get('workflow_key') ?? undefined,
        run_status: searchParams.get('run_status') ?? undefined,
        started_before: searchParams.get('started_before') ?? undefined,
        started_after: searchParams.get('started_after') ?? undefined,
        conversation_id: searchParams.get('conversation_id') ?? undefined,
        cursor: searchParams.get('cursor') ?? undefined,
        limit: searchParams.get('limit') ? Number(searchParams.get('limit')) : undefined,
      },
    });

    return NextResponse.json(response.data ?? { items: [], next_cursor: null });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load workflow runs';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
