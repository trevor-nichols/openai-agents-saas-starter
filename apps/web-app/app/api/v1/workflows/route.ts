import { NextResponse } from 'next/server';

import { listWorkflowsApiV1WorkflowsGet } from '@/lib/api/client/sdk.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

export async function GET() {
  try {
    const { client, auth } = await getServerApiClient();
    const response = await listWorkflowsApiV1WorkflowsGet({
      client,
      auth,
      responseStyle: 'fields',
      throwOnError: true,
    });

    return NextResponse.json(response.data ?? []);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load workflows';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
