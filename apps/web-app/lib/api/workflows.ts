import type {
  PublicSseEvent,
  WorkflowDescriptorResponse,
  WorkflowRunDetail,
  WorkflowRunListResponse,
  WorkflowRunReplayEventsResponse,
  WorkflowRunRequestBody,
  WorkflowRunResponse,
  WorkflowListResponse,
  WorkflowSummary,
  StreamingWorkflowEvent,
} from '@/lib/api/client/types.gen';
import { USE_API_MOCK } from '@/lib/config';
import { collectCursorItems } from '@/lib/api/pagination';
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
import { parseSseStream } from '@/lib/streams/sseParser';

export async function listWorkflows(params?: {
  search?: string | null;
  maxPages?: number;
}): Promise<WorkflowSummary[]> {
  if (USE_API_MOCK) {
    return mockWorkflows;
  }
  return collectCursorItems(
    (cursor) =>
      listWorkflowsPage({
        limit: 100,
        cursor,
        search: params?.search ?? null,
      }),
    { maxPages: params?.maxPages },
  );
}

export async function listWorkflowsPage(params?: {
  limit?: number;
  cursor?: string | null;
  search?: string | null;
}): Promise<WorkflowListResponse> {
  if (USE_API_MOCK) {
    return { items: mockWorkflows, next_cursor: null, total: mockWorkflows.length };
  }

  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set('limit', String(params.limit));
  if (params?.cursor) searchParams.set('cursor', params.cursor);
  if (params?.search) searchParams.set('search', params.search);

  const response = await fetch(
    `${apiV1Path('/workflows')}${searchParams.toString() ? `?${searchParams.toString()}` : ''}`,
    { method: 'GET', cache: 'no-store' },
  );
  if (!response.ok) {
    throw new Error(`Failed to load workflows (${response.status})`);
  }
  const data = (await response.json()) as WorkflowListResponse;
  return {
    items: data.items ?? [],
    next_cursor: data.next_cursor ?? null,
    total: data.total ?? 0,
  };
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
  let terminalSeen = false;

  for await (const evt of parseSseStream(response.body)) {
    const parsed = JSON.parse(evt.data) as unknown;
    if (typeof parsed !== 'object' || parsed === null || !('kind' in parsed)) {
      throw new Error('Unknown stream payload shape');
    }
    const event = parsed as StreamingWorkflowEvent;
    if (!event.kind) {
      throw new Error('Stream event missing kind');
    }
    yield event;
    if (event.kind === 'final' || event.kind === 'error') {
      terminalSeen = true;
      return;
    }
  }

  if (!terminalSeen) {
    throw new Error('Workflow stream ended without a terminal event.');
  }
}

export async function deleteWorkflowRun(runId: string, opts?: { hard?: boolean }): Promise<void> {
  if (USE_API_MOCK) {
    return;
  }
  const query = new URLSearchParams();
  if (opts?.hard) query.set('hard', 'true');

  const response = await fetch(
    apiV1Path(
      `/workflows/runs/${encodeURIComponent(runId)}${query.toString() ? `?${query.toString()}` : ''}`,
    ),
    {
      method: 'DELETE',
    },
  );
  if (!response.ok) {
    let message = `Failed to delete workflow run (${response.status})`;
    let detail: string | undefined;
    try {
      const payload = await response.json();
      detail = typeof payload?.detail === 'string' ? payload.detail : undefined;
      const msgField = typeof payload?.message === 'string' ? payload.message : undefined;
      message = msgField ?? detail ?? message;
    } catch {
      detail = undefined;
      // ignore JSON parse errors; fall back to default message
    }
    const error = new Error(message);
    (error as any).detail = detail;
    (error as any).status = response.status;
    throw error;
  }
}

export async function fetchWorkflowRunReplayEventsPage(params: {
  runId: string;
  limit?: number;
  cursor?: string | null;
}): Promise<WorkflowRunReplayEventsResponse> {
  const { runId, limit, cursor } = params;

  if (USE_API_MOCK) {
    return {
      workflow_run_id: runId,
      conversation_id: 'mock',
      items: [],
      next_cursor: null,
    };
  }

  const searchParams = new URLSearchParams();
  if (limit) searchParams.set('limit', String(limit));
  if (cursor) searchParams.set('cursor', cursor);

  const response = await fetch(
    `${apiV1Path(`/workflows/runs/${encodeURIComponent(runId)}/replay/events`)}${
      searchParams.toString() ? `?${searchParams.toString()}` : ''
    }`,
    { method: 'GET', cache: 'no-store' },
  );

  if (!response.ok) {
    const errorPayload = (await response.json().catch(() => ({}))) as { message?: string };
    throw new Error(errorPayload.message || 'Failed to load workflow run replay events');
  }

  return (await response.json()) as WorkflowRunReplayEventsResponse;
}

export async function fetchWorkflowRunReplayEvents(params: {
  runId: string;
  pageSize?: number;
}): Promise<PublicSseEvent[]> {
  const runId = params.runId;
  const pageSize = Math.min(Math.max(params.pageSize ?? 1000, 1), 1000);

  if (USE_API_MOCK) {
    return [];
  }

  const events: PublicSseEvent[] = [];
  let cursor: string | null = null;

  // Safety guard: prevents accidental infinite loops due to a backend bug.
  const maxPages = 100;
  for (let pageIndex = 0; pageIndex < maxPages; pageIndex += 1) {
    const page = await fetchWorkflowRunReplayEventsPage({ runId, limit: pageSize, cursor });
    events.push(...(page.items ?? []));

    cursor = page.next_cursor ?? null;
    if (!cursor) {
      return events;
    }
  }

  throw new Error('Workflow run replay exceeded maximum page limit');
}
