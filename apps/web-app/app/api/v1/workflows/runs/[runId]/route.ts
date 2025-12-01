import { NextRequest, NextResponse } from 'next/server';

import { getWorkflowRunApiV1WorkflowsRunsRunIdGet } from '@/lib/api/client/sdk.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

export async function GET(_request: NextRequest, context: { params: Promise<{ runId: string }> }) {
  const { runId } = await context.params;
  try {
    const { client, auth } = await getServerApiClient();
    const response = await getWorkflowRunApiV1WorkflowsRunsRunIdGet({
      client,
      auth,
      responseStyle: 'fields',
      throwOnError: true,
      path: { run_id: runId },
    });

    if (!response.data) {
      return NextResponse.json({ message: 'Workflow run not found' }, { status: 404 });
    }

    return NextResponse.json(response.data);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load workflow run';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
