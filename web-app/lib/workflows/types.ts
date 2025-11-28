import type {
  StreamingWorkflowEvent,
  WorkflowRunDetail,
  WorkflowRunRequestBody,
  WorkflowRunResponse,
  WorkflowSummary,
  WorkflowDescriptorResponse,
  WorkflowRunListItem,
  WorkflowRunListResponse,
} from '@/lib/api/client/types.gen';

export type WorkflowSummaryView = WorkflowSummary;
export type WorkflowRunRequest = WorkflowRunRequestBody;
export type WorkflowRun = WorkflowRunResponse;
export type WorkflowRunDetailView = WorkflowRunDetail;
export type WorkflowStreamEvent = StreamingWorkflowEvent;
export type WorkflowDescriptor = WorkflowDescriptorResponse;
export type WorkflowRunListItemView = WorkflowRunListItem;
export type WorkflowRunListView = WorkflowRunListResponse;

export interface WorkflowRunInput {
  workflowKey: string;
  message: string;
  conversationId?: string | null;
  location?: WorkflowRunRequest['location'];
  shareLocation?: boolean | null;
}

export interface WorkflowRunListFilters {
  workflowKey?: string | null;
  runStatus?: 'running' | 'succeeded' | 'failed' | 'cancelled' | string | null;
  startedBefore?: string | null;
  startedAfter?: string | null;
  conversationId?: string | null;
  cursor?: string | null;
  limit?: number;
}
