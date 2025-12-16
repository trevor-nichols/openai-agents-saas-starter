import type {
  WorkflowRun,
  WorkflowRunDetailView,
  WorkflowRunInput,
  WorkflowSummaryView,
  WorkflowDescriptor,
  WorkflowRunListView,
} from './types';
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

export function mockWorkflowDescriptor(key: string): WorkflowDescriptor {
  const base = mockWorkflows.find((w) => w.key === key) ?? mockWorkflows[0];
  if (!base) {
    throw new Error('No mock workflows configured');
  }
  return {
    key: base.key,
    display_name: base.display_name,
    description: base.description,
    default: Boolean(base.default),
    allow_handoff_agents: false,
    step_count: base.step_count,
    output_schema: {
      summary: { type: 'string', description: 'One-line summary of the workflow result' },
      details: { type: 'object', properties: { items: { type: 'array' } } },
    },
    stages: [
      {
        name: 'stage-1',
        mode: 'sequential',
        reducer: null,
        steps: [
          {
            name: 'analyze',
            agent_key: 'analysis',
            guard: null,
            guard_type: null,
            input_mapper: null,
            input_mapper_type: null,
            max_turns: 1,
            output_schema: { summary: { type: 'string' } },
          },
        ],
      },
    ],
  };
}

export function mockRunWorkflow(input: WorkflowRunInput): WorkflowRun {
  return {
    workflow_key: input.workflowKey,
    workflow_run_id: `run_${Date.now()}`,
    conversation_id: input.conversationId ?? `conv_${Date.now()}`,
    steps: [],
    final_output: null,
    output_schema: { summary: { type: 'string' } },
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
    output_schema: { summary: { type: 'string' }, details: { type: 'object' } },
    request_message: 'Example message',
    conversation_id: 'conv-mock',
    steps: [
      {
        name: 'analyze',
        agent_key: 'analysis',
        response_text: 'Identified key intents.',
        structured_output: { intents: ['support', 'pricing'] },
        response_id: 'resp-1',
        stage_name: 'stage-1',
        parallel_group: null,
        branch_index: null,
        output_schema: { intents: { type: 'array', items: { type: 'string' } } },
      },
    ],
  };
}

export function mockWorkflowRunList(): WorkflowRunListView {
  const now = Date.now();
  const baseStarted = new Date(now - 5 * 60_000).toISOString();
  return {
    items: [
      {
        workflow_run_id: 'run-mock-1',
        workflow_key: 'triage-and-summary',
        status: 'succeeded',
        started_at: baseStarted,
        ended_at: new Date(now - 3 * 60_000).toISOString(),
        user_id: 'mock-user',
        conversation_id: 'conv-mock',
        step_count: 3,
        duration_ms: 120000,
        final_output_text: 'All tasks completed.',
      },
      {
        workflow_run_id: 'run-mock-2',
        workflow_key: 'research-pack',
        status: 'running',
        started_at: new Date(now - 1 * 60_000).toISOString(),
        ended_at: null,
        user_id: 'mock-user',
        conversation_id: 'conv-mock-2',
        step_count: 2,
        duration_ms: null,
        final_output_text: null,
      },
    ],
    next_cursor: null,
  };
}

export async function* mockWorkflowStream(runId: string): AsyncGenerator<StreamingWorkflowEvent> {
  const server_timestamp = new Date().toISOString();
  const conversation_id = `conv_${Date.now()}`;
  const response_id = `resp_${Date.now()}`;
  const stream_id = `stream_mock_workflow_${runId}`;
  const workflow_key = 'triage-and-summary';

  const workflow = {
    workflow_key,
    workflow_run_id: runId,
    stage_name: 'main',
    step_name: 'analyze',
    step_agent: 'analysis',
    parallel_group: null,
    branch_index: null,
  } as const;

  yield {
    schema: 'public_sse_v1',
    event_id: 1,
    stream_id,
    server_timestamp,
    kind: 'lifecycle',
    conversation_id,
    response_id,
    agent: 'analysis',
    workflow,
    status: 'in_progress',
  } as StreamingWorkflowEvent;

  yield {
    schema: 'public_sse_v1',
    event_id: 2,
    stream_id,
    server_timestamp,
    kind: 'message.delta',
    conversation_id,
    response_id,
    agent: 'analysis',
    workflow,
    message_id: 'msg_mock_workflow_1',
    delta: 'Working on it...',
  } as StreamingWorkflowEvent;

  yield {
    schema: 'public_sse_v1',
    event_id: 3,
    stream_id,
    server_timestamp,
    kind: 'final',
    conversation_id,
    response_id,
    agent: 'analysis',
    workflow,
    final: {
      status: 'completed',
      response_text: 'Done.',
      structured_output: null,
      reasoning_summary_text: null,
      refusal_text: null,
      attachments: [],
      usage: { input_tokens: 0, output_tokens: 0, total_tokens: 0 },
    },
  } as StreamingWorkflowEvent;
}
