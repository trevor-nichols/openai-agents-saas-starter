import { render, screen } from '@testing-library/react';

import { WorkflowRunConversation } from '../WorkflowRunConversation';
import type { WorkflowRunDetailView } from '@/lib/workflows/types';
import type { PublicSseEvent } from '@/lib/api/client/types.gen';

const run: WorkflowRunDetailView = {
  workflow_key: 'triage_workflow',
  workflow_run_id: 'run-1',
  tenant_id: 'tenant-1',
  user_id: 'user-1',
  status: 'succeeded',
  started_at: new Date().toISOString(),
  ended_at: new Date().toISOString(),
  final_output_text: 'summary',
  final_output_structured: null,
  request_message: 'Hello',
  conversation_id: 'conv-123',
  output_schema: null,
  steps: [],
};

const replayEvents: PublicSseEvent[] = [
  {
    schema: 'public_sse_v1',
    kind: 'lifecycle',
    event_id: 1,
    stream_id: 'stream-replay-test',
    server_timestamp: new Date().toISOString(),
    conversation_id: 'conv-123',
    response_id: 'resp-1',
    agent: 'analysis',
    workflow: {
      workflow_key: 'triage_workflow',
      workflow_run_id: 'run-1',
      stage_name: 'main',
      step_name: 'analysis',
      step_agent: 'researcher',
      parallel_group: null,
      branch_index: null,
    },
    status: 'in_progress',
    reason: null,
    provider_sequence_number: null,
    notices: null,
  },
  {
    schema: 'public_sse_v1',
    kind: 'message.delta',
    event_id: 2,
    stream_id: 'stream-replay-test',
    server_timestamp: new Date().toISOString(),
    conversation_id: 'conv-123',
    response_id: 'resp-1',
    agent: 'analysis',
    workflow: {
      workflow_key: 'triage_workflow',
      workflow_run_id: 'run-1',
      stage_name: 'main',
      step_name: 'analysis',
      step_agent: 'researcher',
      parallel_group: null,
      branch_index: null,
    },
    output_index: 0,
    item_id: 'msg-1',
    content_index: 0,
    delta: 'Hello from replay',
    provider_sequence_number: null,
    notices: null,
  },
];

describe('WorkflowRunConversation', () => {
  it('renders ledger replay events as transcript entries', () => {
    render(
      <WorkflowRunConversation
        run={run}
        replayEvents={replayEvents}
        isLoadingRun={false}
        isLoadingReplay={false}
      />,
    );

    expect(screen.getByText(/hello from replay/i)).toBeInTheDocument();
  });

  it('shows empty state when no run and no events', () => {
    render(
      <WorkflowRunConversation
        run={null}
        replayEvents={null}
        isLoadingRun={false}
        isLoadingReplay={false}
      />,
    );

    expect(screen.getByText(/select a run/i)).toBeInTheDocument();
  });
});
