import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  cancelWorkflowRun,
  getWorkflowDescriptor,
  getWorkflowRun,
  listWorkflowRuns,
  listWorkflows,
  runWorkflow,
  streamWorkflowRun,
  deleteWorkflowRun,
  fetchWorkflowRunReplayEvents,
} from '@/lib/api/workflows';
import type { WorkflowRunInput, WorkflowRunListFilters } from '@/lib/workflows/types';
import type { LocationHint } from '@/lib/api/client/types.gen';
import { queryKeys } from './keys';

export function useWorkflowsQuery() {
  return useQuery({
    queryKey: queryKeys.workflows.list(),
    queryFn: () => listWorkflows(),
  });
}

export function useWorkflowRunQuery(runId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.workflows.run(runId),
    queryFn: () => getWorkflowRun(runId),
    enabled,
  });
}

export function useWorkflowDescriptorQuery(workflowKey: string | null) {
  return useQuery({
    queryKey: queryKeys.workflows.descriptor(workflowKey),
    queryFn: () => (workflowKey ? getWorkflowDescriptor(workflowKey) : null),
    enabled: Boolean(workflowKey),
  });
}

export function useWorkflowRunsQuery(filters: WorkflowRunListFilters) {
  return useQuery({
    queryKey: queryKeys.workflows.runs(filters as Record<string, unknown>),
    queryFn: () => listWorkflowRuns(filters),
    enabled: Boolean(filters.workflowKey),
  });
}

export function useWorkflowRunsInfiniteQuery(filters: WorkflowRunListFilters) {
  return useInfiniteQuery({
    queryKey: queryKeys.workflows.runs(filters as Record<string, unknown>),
    queryFn: ({ pageParam }) => listWorkflowRuns({ ...filters, cursor: (pageParam as string | null | undefined) ?? null }),
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? null,
    enabled: Boolean(filters.workflowKey),
    initialPageParam: null as string | null,
  });
}

export function useWorkflowRunReplayEventsQuery(runId: string | null) {
  return useQuery({
    queryKey: queryKeys.workflows.runReplay(runId),
    queryFn: () => (runId ? fetchWorkflowRunReplayEvents({ runId }) : null),
    enabled: Boolean(runId),
    staleTime: 30_000,
  });
}

export function useRunWorkflowMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: WorkflowRunInput) => runWorkflow(input),
    onSuccess: (data) => {
      if (data.workflow_run_id) {
        queryClient.invalidateQueries({ queryKey: queryKeys.workflows.run(data.workflow_run_id) }).catch(() => {});
      }
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.all }).catch(() => {});
    },
  });
}

export function useCancelWorkflowRunMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (runId: string) => cancelWorkflowRun(runId),
    onSuccess: (_data, runId) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.run(runId) }).catch(() => {});
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.all }).catch(() => {});
    },
  });
}

export async function* useWorkflowStream(
  workflowKey: string,
  body: { message: string; conversation_id?: string | null; location?: LocationHint | null; share_location?: boolean | null },
) {
  yield* streamWorkflowRun(workflowKey, body);
}

export function useDeleteWorkflowRunMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ runId, hard }: { runId: string; hard?: boolean }) =>
      deleteWorkflowRun(runId, { hard }).then(() => ({ runId })),
    onSuccess: ({ runId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.all }).catch(() => {});
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.run(runId) }).catch(() => {});
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.runReplay(runId) }).catch(() => {});
    },
  });
}
