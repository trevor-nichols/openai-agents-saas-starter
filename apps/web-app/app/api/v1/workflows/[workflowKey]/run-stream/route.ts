import { NextResponse } from 'next/server';

import { runWorkflowStreamApiV1WorkflowsWorkflowKeyRunStreamPost } from '@/lib/api/client/sdk.gen';
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

    const upstream = await runWorkflowStreamApiV1WorkflowsWorkflowKeyRunStreamPost({
      client,
      auth,
      signal: request.signal,
      cache: 'no-store',
      responseStyle: undefined,
      throwOnError: true,
      path: { workflow_key: workflowKey },
      body: payload,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
      },
      parseAs: 'stream',
    });

    const stream = upstream.response?.body;
    if (!stream || !upstream.response) {
      return NextResponse.json({ message: 'Workflow stream missing body' }, { status: 500 });
    }

    const headers = new Headers({
      'Content-Type': 'text/event-stream',
      Connection: 'keep-alive',
      'Cache-Control': 'no-cache',
    });

    const contentType = upstream.response.headers.get('Content-Type');
    if (contentType) {
      headers.set('Content-Type', contentType);
    }

    return new Response(stream, {
      status: upstream.response.status,
      statusText: upstream.response.statusText,
      headers,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to stream workflow';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
