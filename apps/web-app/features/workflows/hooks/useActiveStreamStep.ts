'use client';

import type { WorkflowActiveStreamStep, WorkflowStreamEventWithReceivedAt } from '../types';

export function useActiveStreamStep(streamEvents: WorkflowStreamEventWithReceivedAt[]): WorkflowActiveStreamStep {
  for (let i = streamEvents.length - 1; i >= 0; i -= 1) {
    const evt = streamEvents[i];
    if (!evt) continue;
    const workflow = evt.workflow;
    if (workflow?.step_name || workflow?.stage_name || workflow?.parallel_group) {
      return {
        stepName: workflow?.step_name ?? null,
        stageName: workflow?.stage_name ?? null,
        parallelGroup: workflow?.parallel_group ?? null,
        branchIndex: typeof workflow?.branch_index === 'number' ? workflow.branch_index : null,
      };
    }
  }
  return null;
}
