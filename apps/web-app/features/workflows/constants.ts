export const WORKFLOW_STATUS_FILTERS = ['all', 'running', 'succeeded', 'failed', 'cancelled'] as const;

export type WorkflowStatusFilter = (typeof WORKFLOW_STATUS_FILTERS)[number];

export type StreamStatus = 'idle' | 'connecting' | 'streaming' | 'completed' | 'error';
