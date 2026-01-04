import 'server-only';

import {
  cancelWorkflowRunApiV1WorkflowsRunsRunIdCancelPost,
  deleteWorkflowRunApiV1WorkflowsRunsRunIdDelete,
  getWorkflowDescriptorApiV1WorkflowsWorkflowKeyGet,
  getWorkflowRunApiV1WorkflowsRunsRunIdGet,
  getWorkflowRunReplayEventsApiV1WorkflowsRunsRunIdReplayEventsGet,
  listWorkflowRunsApiV1WorkflowsRunsGet,
  listWorkflowsApiV1WorkflowsGet,
  runWorkflowApiV1WorkflowsWorkflowKeyRunPost,
  runWorkflowStreamApiV1WorkflowsWorkflowKeyRunStreamPost,
  streamWorkflowRunReplayEventsApiV1WorkflowsRunsRunIdReplayStreamGet,
} from '@/lib/api/client/sdk.gen';
import type {
  WorkflowDescriptorResponse,
  WorkflowListResponse,
  WorkflowRunDetail,
  WorkflowRunListResponse,
  WorkflowRunReplayEventsResponse,
  WorkflowRunRequestBody,
  WorkflowRunResponse,
} from '@/lib/api/client/types.gen';
import { getServerApiClient } from '../apiClient';

type ApiFieldsResult<TData> =
  | {
      data: TData;
      error: undefined;
      response: Response;
    }
  | {
      data: undefined;
      error: unknown;
      response: Response;
    };

export interface WorkflowApiResult<T> {
  status: number;
  data?: T;
  error?: {
    message: string;
    detail?: string;
  };
}

export interface WorkflowStreamResult {
  status: number;
  stream: ReadableStream<Uint8Array>;
  contentType?: string | null;
}

function resolveErrorDetail(error: unknown): string | undefined {
  if (typeof error === 'string') return error;
  if (error && typeof error === 'object' && 'detail' in error) {
    const detail = (error as { detail?: unknown }).detail;
    return typeof detail === 'string' ? detail : undefined;
  }
  return undefined;
}

export async function listWorkflows(params: {
  limit?: number;
  cursor?: string | null;
  search?: string | null;
}): Promise<WorkflowListResponse> {
  const { client, auth } = await getServerApiClient();
  const response = await listWorkflowsApiV1WorkflowsGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    query: {
      limit: params.limit,
      cursor: params.cursor ?? undefined,
      search: params.search ?? undefined,
    },
  });

  return response.data ?? { items: [], next_cursor: null, total: 0 };
}

export async function getWorkflowDescriptor(
  workflowKey: string,
): Promise<WorkflowDescriptorResponse | null> {
  if (!workflowKey) {
    throw new Error('workflowKey is required.');
  }

  const { client, auth } = await getServerApiClient();
  const response = await getWorkflowDescriptorApiV1WorkflowsWorkflowKeyGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    path: { workflow_key: workflowKey },
  });

  return response.data ?? null;
}

export async function runWorkflow(
  workflowKey: string,
  payload: WorkflowRunRequestBody,
): Promise<WorkflowRunResponse> {
  if (!workflowKey) {
    throw new Error('workflowKey is required.');
  }

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
    throw new Error('Workflow run missing data.');
  }

  return response.data;
}

export async function openWorkflowStream(
  workflowKey: string,
  payload: WorkflowRunRequestBody,
  signal: AbortSignal,
): Promise<WorkflowStreamResult> {
  if (!workflowKey) {
    throw new Error('workflowKey is required.');
  }

  const { client, auth } = await getServerApiClient();
  const upstream = await runWorkflowStreamApiV1WorkflowsWorkflowKeyRunStreamPost({
    client,
    auth,
    signal,
    cache: 'no-store',
    responseStyle: 'fields',
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
    throw new Error('Workflow stream missing body.');
  }

  return {
    status: upstream.response.status,
    stream,
    contentType: upstream.response.headers.get('Content-Type'),
  };
}

export async function listWorkflowRuns(params: {
  workflowKey?: string | null;
  runStatus?: string | null;
  startedBefore?: string | null;
  startedAfter?: string | null;
  conversationId?: string | null;
  cursor?: string | null;
  limit?: number;
}): Promise<WorkflowRunListResponse> {
  const { client, auth } = await getServerApiClient();
  const response = await listWorkflowRunsApiV1WorkflowsRunsGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    query: {
      workflow_key: params.workflowKey ?? undefined,
      run_status: params.runStatus ?? undefined,
      started_before: params.startedBefore ?? undefined,
      started_after: params.startedAfter ?? undefined,
      conversation_id: params.conversationId ?? undefined,
      cursor: params.cursor ?? undefined,
      limit: params.limit,
    },
  });

  return response.data ?? { items: [], next_cursor: null };
}

export async function getWorkflowRun(runId: string): Promise<WorkflowApiResult<WorkflowRunDetail>> {
  if (!runId) {
    return {
      status: 400,
      error: { message: 'runId is required.' },
    };
  }

  const { client, auth } = await getServerApiClient();
  const response = (await getWorkflowRunApiV1WorkflowsRunsRunIdGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: false,
    path: { run_id: runId },
  })) as ApiFieldsResult<WorkflowRunDetail>;

  const status = response.response?.status ?? (response.error ? 500 : 204);
  if (response.error || status >= 400) {
    const detail = resolveErrorDetail(response.error);
    return {
      status,
      error: {
        message: detail ?? 'Failed to load workflow run',
        detail,
      },
    };
  }

  if (!response.data) {
    return {
      status: 404,
      error: { message: 'Workflow run not found' },
    };
  }

  return { status, data: response.data };
}

export async function deleteWorkflowRun(params: {
  runId: string;
  hard: boolean;
  reason?: string;
}): Promise<WorkflowApiResult<null>> {
  if (!params.runId) {
    return {
      status: 400,
      error: { message: 'runId is required.' },
    };
  }

  const { client, auth } = await getServerApiClient();
  const response = (await deleteWorkflowRunApiV1WorkflowsRunsRunIdDelete({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: false,
    path: { run_id: params.runId },
    query: { hard: params.hard, reason: params.reason },
  })) as ApiFieldsResult<null>;

  const status = response.response?.status ?? (response.error ? 500 : 204);
  if (response.error || status >= 400) {
    const detail = resolveErrorDetail(response.error);
    return {
      status,
      error: {
        message: detail ?? 'Failed to delete workflow run',
        detail,
      },
    };
  }

  return { status, data: null };
}

export async function cancelWorkflowRun(runId: string): Promise<void> {
  if (!runId) {
    throw new Error('runId is required.');
  }

  const { client, auth } = await getServerApiClient();
  await cancelWorkflowRunApiV1WorkflowsRunsRunIdCancelPost({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    path: { run_id: runId },
  });
}

export async function getWorkflowRunReplayEvents(params: {
  runId: string;
  cursor?: string;
  limit?: number;
}): Promise<WorkflowApiResult<WorkflowRunReplayEventsResponse>> {
  if (!params.runId) {
    return {
      status: 400,
      error: { message: 'runId is required.' },
    };
  }

  const { client, auth } = await getServerApiClient();
  const response = (await getWorkflowRunReplayEventsApiV1WorkflowsRunsRunIdReplayEventsGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: false,
    path: { run_id: params.runId },
    query: {
      cursor: params.cursor,
      limit: params.limit,
    },
  })) as ApiFieldsResult<WorkflowRunReplayEventsResponse>;

  const status = response.response?.status ?? (response.error ? 500 : 204);
  if (response.error || status >= 400) {
    const detail = resolveErrorDetail(response.error);
    return {
      status,
      error: {
        message: detail ?? 'Failed to load workflow run replay',
        detail,
      },
    };
  }

  if (!response.data) {
    return {
      status: 404,
      error: { message: 'Workflow run replay not found' },
    };
  }

  return { status, data: response.data };
}

export async function openWorkflowReplayStream(params: {
  runId: string;
  cursor?: string;
  signal: AbortSignal;
}): Promise<WorkflowStreamResult> {
  if (!params.runId) {
    throw new Error('runId is required.');
  }

  const { client, auth } = await getServerApiClient();
  const upstream = await streamWorkflowRunReplayEventsApiV1WorkflowsRunsRunIdReplayStreamGet({
    client,
    auth,
    signal: params.signal,
    cache: 'no-store',
    responseStyle: 'fields',
    throwOnError: true,
    path: { run_id: params.runId },
    query: { cursor: params.cursor },
    headers: {
      Accept: 'text/event-stream',
    },
    parseAs: 'stream',
  });

  const stream = upstream.response?.body;
  if (!stream || !upstream.response) {
    throw new Error('Workflow replay stream missing body.');
  }

  return {
    status: upstream.response.status,
    stream,
    contentType: upstream.response.headers.get('Content-Type'),
  };
}
