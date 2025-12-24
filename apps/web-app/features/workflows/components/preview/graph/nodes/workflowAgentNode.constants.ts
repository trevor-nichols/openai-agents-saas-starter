import type { BadgeProps } from '@/components/ui/badge';
import type { NodeStatus } from '@/components/ui/workflow';
import type { WorkflowNodeToolPreviewStatus } from '@/lib/workflows/streaming';

type BadgeTone = Exclude<BadgeProps['variant'], undefined>;

export type WorkflowAgentNodeStatusMeta = {
  title: string;
  description: string;
  badgeTone: BadgeTone;
};

export const WORKFLOW_AGENT_NODE_STATUS_META: Record<NodeStatus, WorkflowAgentNodeStatusMeta> = {
  initial: {
    title: 'Ready',
    description: 'Awaiting execution.',
    badgeTone: 'outline',
  },
  loading: {
    title: 'Running…',
    description: 'Streaming output will appear here.',
    badgeTone: 'outline',
  },
  success: {
    title: 'Completed',
    description: 'This step finished successfully.',
    badgeTone: 'secondary',
  },
  error: {
    title: 'Error',
    description: 'This step failed.',
    badgeTone: 'destructive',
  },
};

const TOOL_STATUS_TONE: Record<WorkflowNodeToolPreviewStatus, BadgeTone> = {
  waiting: 'outline',
  running: 'outline',
  done: 'secondary',
  error: 'destructive',
};

export function toolStatusTone(status: WorkflowNodeToolPreviewStatus): BadgeTone {
  return TOOL_STATUS_TONE[status];
}
