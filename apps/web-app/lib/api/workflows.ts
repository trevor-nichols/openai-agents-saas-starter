import type {
  WorkflowDescriptorResponse,
  WorkflowRunDetail,
  WorkflowRunListResponse,
  WorkflowRunRequestBody,
  WorkflowRunResponse,
  WorkflowSummary,
  StreamingWorkflowEvent,
} from '@/lib/api/client/types.gen';
import { USE_API_MOCK } from '@/lib/config';
import {
  mockRunWorkflow,
  mockWorkflowDescriptor,
  mockWorkflowRunDetail,
  mockWorkflowRunList,
  mockWorkflowStream,
  mockWorkflows,
} from '@/lib/workflows/mock';
import type { WorkflowRunInput, WorkflowRunListFilters } from '@/lib/workflows/types';
import { apiV1Path } from '@/lib/apiPaths';

export async function listWorkflows(): Promise<WorkflowSummary[]> {
  if (USE_API_MOCK) {
    return mockWorkflows;
  }

  // Call the Next.js API proxy so the server can attach auth from cookies.
  const response = await fetch(apiV1Path('/workflows'), { method: 'GET', cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`Failed to load workflows (${response.status})`);
  }
  const data = (await response.json()) as WorkflowSummary[] | undefined;
  return data ?? [];
}

export async function listWorkflowRuns(filters: WorkflowRunListFilters = {}): Promise<WorkflowRunListResponse> {
  if (USE_API_MOCK) {
    return mockWorkflowRunList();
  }

  const query = new URLSearchParams();
  if (filters.workflowKey) query.set('workflow_key', filters.workflowKey);
  if (filters.runStatus) query.set('run_status', filters.runStatus);
  if (filters.startedBefore) query.set('started_before', filters.startedBefore);
  if (filters.startedAfter) query.set('started_after', filters.startedAfter);
  if (filters.conversationId) query.set('conversation_id', filters.conversationId);
  if (filters.cursor) query.set('cursor', filters.cursor);
  if (filters.limit) query.set('limit', String(filters.limit));

  const response = await fetch(apiV1Path(`/workflows/runs?${query.toString()}`), { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`Failed to load workflow runs (${response.status})`);
  }
  return (await response.json()) as WorkflowRunListResponse;
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

  const response = await fetch(apiV1Path(`/workflows/${encodeURIComponent(input.workflowKey)}/run`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(`Failed to run workflow (${response.status})`);
  }

  return (await response.json()) as WorkflowRunResponse;
}

export async function getWorkflowRun(runId: string): Promise<WorkflowRunDetail> {
  if (USE_API_MOCK) {
    return mockWorkflowRunDetail(runId);
  }
  const response = await fetch(apiV1Path(`/workflows/runs/${encodeURIComponent(runId)}`), { cache: 'no-store' });
  if (response.status === 404) {
    throw new Error('Workflow run not found');
  }
  if (!response.ok) {
    throw new Error(`Failed to load workflow run (${response.status})`);
  }
  return (await response.json()) as WorkflowRunDetail;
}

export async function cancelWorkflowRun(runId: string): Promise<void> {
  if (USE_API_MOCK) {
    return;
  }
  const response = await fetch(apiV1Path(`/workflows/runs/${encodeURIComponent(runId)}/cancel`), {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error(`Failed to cancel workflow run (${response.status})`);
  }
}

export async function getWorkflowDescriptor(workflowKey: string): Promise<WorkflowDescriptorResponse> {
  if (USE_API_MOCK) {
    return mockWorkflowDescriptor(workflowKey);
  }
  const response = await fetch(apiV1Path(`/workflows/${encodeURIComponent(workflowKey)}`), { cache: 'no-store' });
  if (response.status === 404) {
    throw new Error('Workflow not found');
  }
  if (!response.ok) {
    throw new Error(`Failed to load workflow descriptor (${response.status})`);
  }
  return (await response.json()) as WorkflowDescriptorResponse;
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

  const response = await fetch(apiV1Path(`/workflows/${encodeURIComponent(workflowKey)}/run-stream`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify(body),
  });

  if (!response.ok || !response.body) {
    throw new Error('Workflow stream response missing body');
  }

  const reader = response.body.getReader();
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
