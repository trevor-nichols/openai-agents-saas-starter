import type {
  StreamingWorkflowEvent,
  WorkflowRunDetail,
  WorkflowRunRequestBody,
  WorkflowRunResponse,
  WorkflowSummary,
} from '@/lib/api/client/types.gen';

export type WorkflowSummaryView = WorkflowSummary;
export type WorkflowRunRequest = WorkflowRunRequestBody;
export type WorkflowRun = WorkflowRunResponse;
export type WorkflowRunDetailView = WorkflowRunDetail;
export type WorkflowStreamEvent = StreamingWorkflowEvent;

export interface WorkflowRunInput {
  workflowKey: string;
  message: string;
  conversationId?: string | null;
  location?: WorkflowRunRequest['location'];
  shareLocation?: boolean | null;
}
