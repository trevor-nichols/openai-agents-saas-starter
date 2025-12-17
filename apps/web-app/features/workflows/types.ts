import type { StreamingWorkflowEvent } from '@/lib/api/client/types.gen';

export type WorkflowStreamEventWithReceivedAt = StreamingWorkflowEvent & { receivedAt: string };

export type WorkflowRunSummary = {
  workflowKey: string;
  runId?: string | null;
  message?: string;
};

