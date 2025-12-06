import { act, renderHook, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';

import { useWorkflowSelection, useWorkflowRunStream, useWorkflowRunsInfinite } from '../index';
import { createQueryWrapper } from '@/lib/chat/__tests__/testUtils';
import type { WorkflowRunListResponse, StreamingWorkflowEvent } from '@/lib/api/client/types.gen';

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
        kind: 'lifecycle',
        workflow_run_id: 'run-123',
        workflow_key: 'wf-1',
        is_terminal: false,
      },
      {
        kind: 'lifecycle',
        workflow_run_id: 'run-123',
        workflow_key: 'wf-1',
        is_terminal: true,
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
        workflow_run_id: 'run-err',
        workflow_key: 'wf-err',
        is_terminal: true,
        payload: { message: 'boom' },
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
