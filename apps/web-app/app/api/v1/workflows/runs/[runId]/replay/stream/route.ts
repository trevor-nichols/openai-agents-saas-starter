import { NextResponse } from 'next/server';

import { streamWorkflowRunReplayEventsApiV1WorkflowsRunsRunIdReplayStreamGet } from '@/lib/api/client/sdk.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

export async function GET(request: Request, context: { params: Promise<{ runId: string }> }) {
  const { runId } = await context.params;
  const { searchParams } = new URL(request.url);
  const cursor = searchParams.get('cursor') ?? undefined;

  try {
    const { client, auth } = await getServerApiClient();

    const upstream = await streamWorkflowRunReplayEventsApiV1WorkflowsRunsRunIdReplayStreamGet({
      client,
      auth,
      signal: request.signal,
      cache: 'no-store',
      responseStyle: undefined,
      throwOnError: true,
      path: { run_id: runId },
      query: { cursor },
      headers: {
        Accept: 'text/event-stream',
      },
      parseAs: 'stream',
    });

    const stream = upstream.response?.body;
    if (!stream || !upstream.response) {
      return NextResponse.json({ message: 'Workflow replay stream missing body' }, { status: 500 });
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
    const message = error instanceof Error ? error.message : 'Failed to stream workflow replay';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}

