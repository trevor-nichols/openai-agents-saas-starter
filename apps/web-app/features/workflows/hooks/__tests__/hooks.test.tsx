import { act, renderHook, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';

import {
  useActiveStreamStep,
  useWorkflowCapabilities,
  useWorkflowOverrides,
  useWorkflowRunLauncher,
  useWorkflowSelection,
  useWorkflowRunStream,
  useWorkflowRunsInfinite,
} from '../index';
import { createQueryWrapper } from '@/lib/chat/__tests__/testUtils';
import type { ToolRegistry } from '@/types/tools';
import type { WorkflowDescriptor } from '@/lib/workflows/types';
import type { WorkflowRunListResponse, StreamingWorkflowEvent } from '@/lib/api/client/types.gen';
import type { WorkflowStreamEventWithReceivedAt } from '../../types';

const replaceMock = vi.fn();
let searchParamsValue = '';

vi.mock('next/navigation', () => ({
  usePathname: () => '/app/workflows',
  useRouter: () => ({ replace: replaceMock }),
  useSearchParams: () => new URLSearchParams(searchParamsValue),
}));

vi.mock('@/lib/api/workflows', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api/workflows')>();
  return {
    ...actual,
    listWorkflowRuns: vi.fn(),
    streamWorkflowRun: vi.fn(),
  };
});

const { listWorkflowRuns, streamWorkflowRun } = vi.mocked(await import('@/lib/api/workflows'));

beforeEach(() => {
  replaceMock.mockReset();
  searchParamsValue = '';
  vi.clearAllMocks();
});

afterEach(() => {
  vi.clearAllMocks();
});

describe('useWorkflowSelection', () => {
  it('auto-selects first workflow when URL lacks workflow param', async () => {
    const { result } = renderHook(() => useWorkflowSelection(['wf-1', 'wf-2']));

    await waitFor(() => expect(replaceMock).toHaveBeenCalled());
    expect(replaceMock).toHaveBeenCalledWith('/app/workflows?workflow=wf-1', { scroll: false });

    act(() => result.current.setRun('run-9'));
    expect(replaceMock).toHaveBeenLastCalledWith('/app/workflows?workflow=wf-1&run=run-9', { scroll: false });
  });

  it('respects existing workflow in URL and updates run param', async () => {
    searchParamsValue = 'workflow=wf-existing';
    const { result } = renderHook(() => useWorkflowSelection(['wf-1', 'wf-2']));

    expect(result.current.selectedWorkflowKey).toBe('wf-existing');
    act(() => result.current.setRun('run-1'));
    expect(replaceMock).toHaveBeenLastCalledWith('/app/workflows?workflow=wf-existing&run=run-1', { scroll: false });
  });

  it('resetRun clears run while preserving workflow', () => {
    searchParamsValue = 'workflow=wf-keep&run=run-old';
    const { result } = renderHook(() => useWorkflowSelection(['wf-keep', 'wf-2']));

    act(() => result.current.resetRun());
    expect(replaceMock).toHaveBeenLastCalledWith('/app/workflows?workflow=wf-keep', { scroll: false });
  });

  it('setWorkflow rewrites workflow and clears run', () => {
    searchParamsValue = 'workflow=wf-old&run=run-old';
    const { result } = renderHook(() => useWorkflowSelection(['wf-old', 'wf-new']));

    act(() => result.current.setWorkflow('wf-new'));
    expect(replaceMock).toHaveBeenLastCalledWith('/app/workflows?workflow=wf-new', { scroll: false });
  });
});

describe('useWorkflowRunStream', () => {
  it('auto-selects newly created run via callback and reaches completed status', async () => {
    const events: StreamingWorkflowEvent[] = [
      {
        schema: 'public_sse_v1',
        event_id: 1,
        stream_id: 'stream-wf',
        server_timestamp: '2025-12-15T00:00:00.000Z',
        kind: 'lifecycle',
        conversation_id: 'conv-1',
        response_id: 'resp-1',
        agent: 'triage',
        workflow: {
          workflow_key: 'wf-1',
          workflow_run_id: 'run-123',
          stage_name: 'main',
          step_name: 'step-1',
          step_agent: 'triage',
          parallel_group: null,
          branch_index: null,
        },
        status: 'in_progress',
      },
      {
        schema: 'public_sse_v1',
        event_id: 2,
        stream_id: 'stream-wf',
        server_timestamp: '2025-12-15T00:00:00.050Z',
        kind: 'final',
        conversation_id: 'conv-1',
        response_id: 'resp-1',
        agent: 'triage',
        workflow: {
          workflow_key: 'wf-1',
          workflow_run_id: 'run-123',
          stage_name: 'main',
          step_name: 'step-1',
          step_agent: 'triage',
          parallel_group: null,
          branch_index: null,
        },
        final: {
          status: 'completed',
          response_text: 'done',
          structured_output: null,
          reasoning_summary_text: null,
          refusal_text: null,
          attachments: [],
          usage: { input_tokens: 1, output_tokens: 1, total_tokens: 2 },
        },
      },
    ];

    streamWorkflowRun.mockImplementation(async function* () {
      for (const evt of events) yield evt as StreamingWorkflowEvent;
    });

    const onRunCreated = vi.fn();
    const { result } = renderHook(() => useWorkflowRunStream({ onRunCreated }));

    await act(async () => {
      await result.current.startRun({ workflowKey: 'wf-1', message: 'hello' });
    });

    expect(onRunCreated).toHaveBeenCalledTimes(1);
    expect(onRunCreated).toHaveBeenCalledWith('run-123', 'wf-1');
    expect(result.current.status).toBe('completed');
    expect(result.current.events).toHaveLength(2);
    expect(result.current.lastSummary?.runId).toBe('run-123');
    expect(result.current.lastUpdated).toBeTruthy();
  });

  it('surfaces error event payload message and sets status error', async () => {
    const events: StreamingWorkflowEvent[] = [
      {
        kind: 'error',
        schema: 'public_sse_v1',
        event_id: 1,
        stream_id: 'stream-wf-err',
        server_timestamp: '2025-12-15T00:00:00.000Z',
        conversation_id: 'conv-err',
        response_id: null,
        agent: 'triage',
        workflow: {
          workflow_key: 'wf-err',
          workflow_run_id: 'run-err',
          stage_name: 'main',
          step_name: 'step-1',
          step_agent: 'triage',
          parallel_group: null,
          branch_index: null,
        },
        error: { code: 'boom', message: 'boom', source: 'server', is_retryable: false },
      },
    ];
    streamWorkflowRun.mockImplementation(async function* () {
      for (const evt of events) yield evt as StreamingWorkflowEvent;
    });

    const { result } = renderHook(() => useWorkflowRunStream());
    await act(async () => {
      await result.current.startRun({ workflowKey: 'wf-err', message: 'hello' });
    });

    expect(result.current.status).toBe('error');
    expect(result.current.error).toBe('boom');
    expect(result.current.events).toHaveLength(1);
  });

  it('handles thrown stream errors and does not invoke onRunCreated', async () => {
    streamWorkflowRun.mockImplementation(async function* () {
      throw new Error('network down');
    });
    const onRunCreated = vi.fn();
    const { result } = renderHook(() => useWorkflowRunStream({ onRunCreated }));

    await act(async () => {
      await result.current.startRun({ workflowKey: 'wf-err', message: 'hi' });
    });

    expect(onRunCreated).not.toHaveBeenCalled();
    expect(result.current.status).toBe('error');
    expect(result.current.error).toBe('network down');
    expect(result.current.events).toHaveLength(0);
  });
});

describe('useWorkflowRunsInfinite', () => {
  it('paginates and exposes hasMore based on next_cursor', async () => {
    const firstPage: WorkflowRunListResponse = {
      items: [
        {
          workflow_run_id: 'run-1',
          workflow_key: 'wf-1',
          status: 'running',
          started_at: '2025-01-01T00:00:00.000Z',
          ended_at: null,
          user_id: 'user-1',
          step_count: 1,
        },
      ],
      next_cursor: 'cursor-1',
    };
    const secondPage: WorkflowRunListResponse = {
      items: [
        {
          workflow_run_id: 'run-2',
          workflow_key: 'wf-1',
          status: 'succeeded',
          started_at: '2025-01-02T00:00:00.000Z',
          ended_at: '2025-01-02T01:00:00.000Z',
          user_id: 'user-1',
          step_count: 2,
        },
      ],
      next_cursor: null,
    };

    listWorkflowRuns.mockResolvedValueOnce(firstPage);
    listWorkflowRuns.mockResolvedValueOnce(secondPage);

    const { Wrapper } = createQueryWrapper();
    const { result } = renderHook(
      () => useWorkflowRunsInfinite({ workflowKey: 'wf-1', limit: 20 }),
      { wrapper: Wrapper },
    );

    await waitFor(() => expect(result.current.isInitialLoading).toBe(false));
    expect(result.current.runs.map((r) => r.workflow_run_id)).toEqual(['run-1']);
    expect(result.current.hasMore).toBe(true);

    await act(async () => {
      await result.current.loadMore?.();
    });

    await waitFor(() => expect(result.current.runs.map((r) => r.workflow_run_id)).toEqual(['run-1', 'run-2']));
    expect(result.current.hasMore).toBe(false);

    expect(listWorkflowRuns).toHaveBeenNthCalledWith(1, { workflowKey: 'wf-1', runStatus: undefined, cursor: null, limit: 20 });
    expect(listWorkflowRuns).toHaveBeenNthCalledWith(2, { workflowKey: 'wf-1', runStatus: undefined, cursor: 'cursor-1', limit: 20 });
  });

  it('returns no loadMore when server signals end of list', async () => {
    const singlePage: WorkflowRunListResponse = {
      items: [
        {
          workflow_run_id: 'run-1',
          workflow_key: 'wf-1',
          status: 'succeeded',
          started_at: '2025-01-01T00:00:00.000Z',
          ended_at: '2025-01-01T00:10:00.000Z',
          user_id: 'user-1',
          step_count: 1,
        },
      ],
      next_cursor: null,
    };

    listWorkflowRuns.mockResolvedValueOnce(singlePage);

    const { Wrapper } = createQueryWrapper();
    const { result } = renderHook(
      () => useWorkflowRunsInfinite({ workflowKey: 'wf-1', limit: 20 }),
      { wrapper: Wrapper },
    );

    await waitFor(() => expect(result.current.isInitialLoading).toBe(false));
    expect(result.current.hasMore).toBe(false);
    expect(result.current.loadMore).toBeUndefined();
  });
});

describe('useWorkflowOverrides', () => {
  it('stores overrides per workflow and switches between selections', () => {
    const { result, rerender } = renderHook(
      ({ workflowKey }) => useWorkflowOverrides(workflowKey),
      { initialProps: { workflowKey: 'wf-1' } },
    );

    act(() => result.current.setContainerOverride('agent-1', 'container-1'));
    act(() => result.current.setVectorStoreOverride('agent-1', 'vs-1'));
    expect(result.current.containerOverrides).toEqual({ 'agent-1': 'container-1' });
    expect(result.current.vectorStoreOverrides).toEqual({ 'agent-1': 'vs-1' });

    rerender({ workflowKey: 'wf-2' });
    expect(result.current.containerOverrides).toEqual({});
    expect(result.current.vectorStoreOverrides).toEqual({});

    act(() => result.current.setContainerOverride('agent-2', 'container-2'));
    rerender({ workflowKey: 'wf-1' });
    expect(result.current.containerOverrides).toEqual({ 'agent-1': 'container-1' });
    expect(result.current.vectorStoreOverrides).toEqual({ 'agent-1': 'vs-1' });
  });
});

describe('useActiveStreamStep', () => {
  it('returns the latest event with step metadata', () => {
    const baseEvent: StreamingWorkflowEvent = {
      schema: 'public_sse_v1',
      event_id: 1,
      stream_id: 'stream-1',
      server_timestamp: '2025-12-15T00:00:00.000Z',
      kind: 'lifecycle',
      conversation_id: 'conv-1',
      response_id: null,
      agent: 'triage',
      workflow: {
        workflow_key: 'wf-1',
        workflow_run_id: 'run-1',
        stage_name: 'stage-1',
        step_name: 'step-1',
        step_agent: 'triage',
        parallel_group: null,
        branch_index: null,
      },
      status: 'in_progress',
    };

    const events: WorkflowStreamEventWithReceivedAt[] = [
      { ...baseEvent, receivedAt: '2025-12-15T00:00:00.010Z' },
      {
        ...baseEvent,
        event_id: 2,
        workflow: { ...baseEvent.workflow, stage_name: 'stage-2', step_name: 'step-2' },
        receivedAt: '2025-12-15T00:00:00.020Z',
      },
    ];

    const { result } = renderHook(() => useActiveStreamStep(events));
    expect(result.current).toEqual({
      stepName: 'step-2',
      stageName: 'stage-2',
      parallelGroup: null,
      branchIndex: null,
    });
  });

  it('returns null when no event carries step metadata', () => {
    const events: WorkflowStreamEventWithReceivedAt[] = [
      {
        schema: 'public_sse_v1',
        event_id: 1,
        stream_id: 'stream-2',
        server_timestamp: '2025-12-15T00:00:00.000Z',
        kind: 'lifecycle',
        conversation_id: 'conv-2',
        response_id: null,
        agent: 'triage',
        workflow: {
          workflow_key: 'wf-2',
          workflow_run_id: 'run-2',
          stage_name: null,
          step_name: null,
          step_agent: 'triage',
          parallel_group: null,
          branch_index: null,
        },
        status: 'in_progress',
        receivedAt: '2025-12-15T00:00:00.010Z',
      },
    ];

    const { result } = renderHook(() => useActiveStreamStep(events));
    expect(result.current).toBeNull();
  });
});

describe('useWorkflowRunLauncher', () => {
  it('filters overrides by supported agents and runs follow-up action', async () => {
    const startRun = vi.fn().mockResolvedValue(undefined);
    const onAfterRun = vi.fn();

    const { result } = renderHook(() =>
      useWorkflowRunLauncher({
        startRun,
        containerOverrides: { 'agent-a': 'container-a', 'agent-b': 'container-b', 'agent-c': null },
        vectorStoreOverrides: { 'agent-a': 'vs-a', 'agent-b': 'vs-b' },
        supportsContainersByAgent: { 'agent-a': true, 'agent-b': false },
        supportsFileSearchByAgent: { 'agent-a': false, 'agent-b': true },
        onAfterRun,
      }),
    );

    await act(async () => {
      await result.current({ workflowKey: 'wf-1', message: 'hello' });
    });

    expect(startRun).toHaveBeenCalledWith({
      workflowKey: 'wf-1',
      message: 'hello',
      containerOverrides: { 'agent-a': 'container-a' },
      vectorStoreOverrides: { 'agent-b': { vector_store_id: 'vs-b' } },
    });
    expect(onAfterRun).toHaveBeenCalledTimes(1);
  });
});

describe('useWorkflowCapabilities', () => {
  it('maps agent tools and capability flags from descriptor + registry', () => {
    const descriptor: WorkflowDescriptor = {
      key: 'wf-1',
      display_name: 'Demo',
      description: 'desc',
      default: false,
      allow_handoff_agents: false,
      step_count: 2,
      stages: [
        {
          name: 'stage-1',
          mode: 'sequential',
          steps: [
            { name: 'step-1', agent_key: 'agent-a' },
            { name: 'step-2', agent_key: 'agent-b' },
          ],
        },
      ],
      output_schema: null,
    };

    const tools: ToolRegistry = {
      total_tools: 2,
      tool_names: ['file_search', 'code_interpreter'],
      per_agent: {
        'agent-a': ['file_search'],
        'agent-b': ['code_interpreter'],
      },
    };

    const { result } = renderHook(() => useWorkflowCapabilities(descriptor, tools));

    expect(result.current.toolsByAgent['agent-a']).toEqual(['file_search']);
    expect(result.current.toolsByAgent['agent-b']).toEqual(['code_interpreter']);
    expect(result.current.supportsFileSearchByAgent['agent-a']).toBe(true);
    expect(result.current.supportsContainersByAgent['agent-a']).toBe(false);
    expect(result.current.supportsFileSearchByAgent['agent-b']).toBe(false);
    expect(result.current.supportsContainersByAgent['agent-b']).toBe(true);
  });
});
