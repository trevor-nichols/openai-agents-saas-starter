import {
  getWorkflowRunApiV1WorkflowsRunsRunIdGet,
  listWorkflowsApiV1WorkflowsGet,
  runWorkflowApiV1WorkflowsWorkflowKeyRunPost,
  runWorkflowStreamApiV1WorkflowsWorkflowKeyRunStreamPost,
} from '@/lib/api/client/sdk.gen';
import type {
  WorkflowRunRequestBody,
  WorkflowRunResponse,
  WorkflowSummary,
  StreamingWorkflowEvent,
} from '@/lib/api/client/types.gen';
import { USE_API_MOCK } from '@/lib/config';
import { mockRunWorkflow, mockWorkflowRunDetail, mockWorkflowStream, mockWorkflows } from '@/lib/workflows/mock';
import type { WorkflowRunInput } from '@/lib/workflows/types';

import { client } from './config';

export async function listWorkflows(): Promise<WorkflowSummary[]> {
  if (USE_API_MOCK) {
    return mockWorkflows;
  }
  const response = await listWorkflowsApiV1WorkflowsGet({ client, throwOnError: true, responseStyle: 'fields' });
  return response.data ?? [];
}

export async function runWorkflow(input: WorkflowRunInput): Promise<WorkflowRunResponse> {
  if (USE_API_MOCK) {
    return mockRunWorkflow(input);
  }
  const body: WorkflowRunRequestBody = {
    message: input.message,
    conversation_id: input.conversationId ?? undefined,
    location: input.location,
    share_location: input.shareLocation ?? null,
  };
  const response = await runWorkflowApiV1WorkflowsWorkflowKeyRunPost({
    client,
    throwOnError: true,
    responseStyle: 'fields',
    path: { workflow_key: input.workflowKey },
    body,
  });
  if (!response.data) {
    throw new Error('Workflow run response missing data');
  }
  return response.data;
}

export async function getWorkflowRun(runId: string) {
  if (USE_API_MOCK) {
    return mockWorkflowRunDetail(runId);
  }
  const response = await getWorkflowRunApiV1WorkflowsRunsRunIdGet({
    client,
    throwOnError: true,
    responseStyle: 'fields',
    path: { run_id: runId },
  });
  if (!response.data) {
    throw new Error('Workflow run detail missing data');
  }
  return response.data;
}

export async function* streamWorkflowRun(
  workflowKey: string,
  body: WorkflowRunRequestBody,
): AsyncGenerator<StreamingWorkflowEvent> {
  if (USE_API_MOCK) {
    const mockRunId = `run_${Date.now()}`;
    yield* mockWorkflowStream(mockRunId);
    return;
  }

  const response = await runWorkflowStreamApiV1WorkflowsWorkflowKeyRunStreamPost({
    client,
    throwOnError: true,
    responseStyle: undefined,
    path: { workflow_key: workflowKey },
    body,
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    parseAs: 'stream',
  });

  const stream = response.response?.body;
  if (!stream) {
    throw new Error('Workflow stream response missing body');
  }

  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const segments = buffer.split('\n\n');
      buffer = segments.pop() ?? '';

      for (const segment of segments) {
        if (!segment.trim() || !segment.startsWith('data: ')) continue;
        const data = JSON.parse(segment.slice(6)) as StreamingWorkflowEvent;
        yield data;
        if (data.is_terminal) return;
      }
    }
  } finally {
    reader.releaseLock();
  }
}
