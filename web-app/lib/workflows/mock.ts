import type { WorkflowRun, WorkflowRunDetailView, WorkflowRunInput, WorkflowSummaryView } from './types';
import type { StreamingWorkflowEvent } from '@/lib/api/client/types.gen';

export const mockWorkflows: WorkflowSummaryView[] = [
  {
    key: 'triage-and-summary',
    display_name: 'Triage & Summarize',
    description: 'Classify intent, route to agent, and produce a short summary.',
    step_count: 3,
    default: true,
  },
  {
    key: 'research-pack',
    display_name: 'Research Pack',
    description: 'Web search, synthesize findings, and list sources.',
    step_count: 4,
    default: false,
  },
];

export function mockRunWorkflow(input: WorkflowRunInput): WorkflowRun {
  return {
    workflow_key: input.workflowKey,
    workflow_run_id: `run_${Date.now()}`,
    conversation_id: input.conversationId ?? `conv_${Date.now()}`,
    steps: [],
    final_output: null,
  };
}

export function mockWorkflowRunDetail(runId: string): WorkflowRunDetailView {
  return {
    workflow_key: 'triage-and-summary',
    workflow_run_id: runId,
    tenant_id: 'mock-tenant',
    user_id: 'mock-user',
    status: 'completed',
    started_at: new Date(Date.now() - 60_000).toISOString(),
    ended_at: new Date().toISOString(),
    final_output_text: 'All tasks completed.',
    final_output_structured: { summary: 'All good.' },
    request_message: 'Example message',
    conversation_id: 'conv-mock',
    steps: [],
  };
}

export async function* mockWorkflowStream(runId: string): AsyncGenerator<StreamingWorkflowEvent> {
  const base = {
    workflow_key: 'triage-and-summary',
    workflow_run_id: runId,
  } as const;

  yield {
    ...base,
    kind: 'lifecycle',
    workflow_run_id: runId,
    workflow_key: base.workflow_key,
    event: 'run_started',
    is_terminal: false,
  } as StreamingWorkflowEvent;

  yield {
    ...base,
    kind: 'run_item',
    run_item_name: 'agent_output',
    run_item_type: 'agent',
    agent: 'researcher',
    response_id: 'resp-1',
    sequence_number: 1,
    response_text: 'Working on it...',
    structured_output: null,
    is_terminal: false,
  } as StreamingWorkflowEvent;

  yield {
    ...base,
    kind: 'raw_response',
    raw_type: 'response.output_text.delta',
    text_delta: 'Done.',
    sequence_number: 2,
    is_terminal: false,
  } as StreamingWorkflowEvent;

  yield {
    ...base,
    kind: 'raw_response',
    raw_type: 'response.completed',
    text_delta: '',
    sequence_number: 3,
    is_terminal: true,
  } as StreamingWorkflowEvent;
}
