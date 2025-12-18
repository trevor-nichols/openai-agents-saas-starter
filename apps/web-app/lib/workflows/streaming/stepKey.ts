import type { WorkflowContext } from '@/lib/api/client/types.gen';

export type WorkflowNodeIdentity = Readonly<{
  stageName: string;
  stepName: string | null;
  branchIndex: number | null;
}>;

export type WorkflowNodeContextKey = WorkflowNodeIdentity &
  Readonly<{
    stepAgent: string | null;
  }>;

export type SerializedWorkflowNodeIdentity = string;

function normalizeNullableString(value: unknown): string | null {
  if (typeof value !== 'string') return null;
  const trimmed = value.trim();
  return trimmed.length ? trimmed : null;
}

/**
 * Extract the workflow step identity from the public SSE workflow context.
 *
 * Canonical identity is stage + step + branch (agent is intentionally not part of the primary key).
 */
export function contextKeyFromWorkflowContext(context: WorkflowContext | null | undefined): WorkflowNodeContextKey | null {
  if (!context) return null;
  const stageName = normalizeNullableString(context.stage_name) ?? normalizeNullableString(context.parallel_group);
  if (!stageName) return null;

  return {
    stageName,
    stepName: normalizeNullableString(context.step_name),
    branchIndex: typeof context.branch_index === 'number' ? context.branch_index : null,
    stepAgent: normalizeNullableString(context.step_agent),
  };
}

export function serializeWorkflowNodeIdentity(identity: WorkflowNodeIdentity): SerializedWorkflowNodeIdentity {
  // Use a delimiter that is unlikely to appear in workflow names.
  return [
    identity.stageName,
    identity.stepName ?? '',
    identity.branchIndex ?? '',
  ].join('::');
}

export function serializeStageBranchKey(params: {
  stageName: string;
  branchIndex: number;
}): string {
  return [params.stageName, params.branchIndex].join('::');
}

export function serializeStageAgentBranchKey(params: {
  stageName: string;
  stepAgent: string;
  branchIndex: number | null;
}): string {
  return [params.stageName, params.stepAgent, params.branchIndex ?? ''].join('::');
}

