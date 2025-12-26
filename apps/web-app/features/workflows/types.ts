import type { LocationHint, StreamingWorkflowEvent } from '@/lib/api/client/types.gen';

export type WorkflowStreamEventWithReceivedAt = StreamingWorkflowEvent & { receivedAt: string };

export type WorkflowRunSummary = {
  workflowKey: string;
  runId?: string | null;
  message?: string;
};

export type WorkflowRunLaunchInput = {
  workflowKey: string;
  message: string;
  shareLocation?: boolean;
  location?: LocationHint | null;
};

export type WorkflowRunStartInput = WorkflowRunLaunchInput & {
  containerOverrides?: Record<string, string> | null;
  vectorStoreOverrides?: Record<string, { vector_store_id: string }> | null;
};

export type WorkflowActiveStreamStep = {
  stepName: string | null;
  stageName: string | null;
  parallelGroup: string | null;
  branchIndex: number | null;
} | null;
