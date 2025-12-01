import { NextResponse } from 'next/server';

import { getWorkflowDescriptorApiV1WorkflowsWorkflowKeyGet } from '@/lib/api/client/sdk.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

export async function GET(_: Request, { params }: { params: Promise<{ workflowKey: string }> }) {
  const { workflowKey } = await params;
  try {
    const { client, auth } = await getServerApiClient();
    const response = await getWorkflowDescriptorApiV1WorkflowsWorkflowKeyGet({
      client,
      auth,
      responseStyle: 'fields',
      throwOnError: true,
      path: { workflow_key: workflowKey },
    });

    if (!response.data) {
      return NextResponse.json({ message: 'Workflow not found' }, { status: 404 });
    }

    return NextResponse.json(response.data);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load workflow descriptor';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
