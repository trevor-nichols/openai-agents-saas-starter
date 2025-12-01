import { NextResponse } from 'next/server';

import { runWorkflowApiV1WorkflowsWorkflowKeyRunPost } from '@/lib/api/client/sdk.gen';
import type { WorkflowRunRequestBody } from '@/lib/api/client/types.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

export async function POST(
  request: Request,
  { params }: { params: Promise<{ workflowKey: string }> },
) {
  const { workflowKey } = await params;
  try {
    const payload = (await request.json()) as WorkflowRunRequestBody;
    const { client, auth } = await getServerApiClient();
    const response = await runWorkflowApiV1WorkflowsWorkflowKeyRunPost({
      client,
      auth,
      responseStyle: 'fields',
      throwOnError: true,
      path: { workflow_key: workflowKey },
      body: payload,
    });

    if (!response.data) {
      return NextResponse.json({ message: 'Workflow run missing data' }, { status: 500 });
    }

    return NextResponse.json(response.data);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to start workflow';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
