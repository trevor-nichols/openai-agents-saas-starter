import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { getWorkflowRun, listWorkflows, runWorkflow, streamWorkflowRun } from '@/lib/api/workflows';
import type { WorkflowRunInput } from '@/lib/workflows/types';
import type { LocationHint } from '@/lib/api/client/types.gen';
import { queryKeys } from './keys';

export function useWorkflowsQuery() {
  return useQuery({
    queryKey: queryKeys.workflows.list(),
    queryFn: listWorkflows,
  });
}

export function useWorkflowRunQuery(runId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.workflows.run(runId),
    queryFn: () => getWorkflowRun(runId),
    enabled,
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
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.list() }).catch(() => {});
    },
  });
}

export async function* useWorkflowStream(
  workflowKey: string,
  body: { message: string; conversation_id?: string | null; location?: LocationHint | null; share_location?: boolean | null },
) {
  yield* streamWorkflowRun(workflowKey, body);
}
