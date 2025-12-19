export const WORKFLOW_STATUS_FILTERS = ['all', 'running', 'succeeded', 'failed', 'cancelled'] as const;

export type WorkflowStatusFilter = (typeof WORKFLOW_STATUS_FILTERS)[number];

export type StreamStatus = 'idle' | 'connecting' | 'streaming' | 'completed' | 'error';

type StatusBadgeVariant = 'default' | 'secondary' | 'outline' | 'destructive';

const WORKFLOW_RUN_STATUS_VARIANT: Record<string, StatusBadgeVariant> = {
  running: 'default',
  succeeded: 'secondary',
  failed: 'destructive',
  cancelled: 'outline',
};

export function workflowRunStatusVariant(status: string): StatusBadgeVariant {
  return WORKFLOW_RUN_STATUS_VARIANT[status] ?? 'outline';
}
