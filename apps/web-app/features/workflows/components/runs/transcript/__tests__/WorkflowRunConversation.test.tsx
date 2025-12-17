import { render, screen } from '@testing-library/react';

import { WorkflowRunConversation } from '../WorkflowRunConversation';
import type { WorkflowRunDetailView } from '@/lib/workflows/types';
import type { ConversationEvents } from '@/types/conversations';

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

const events: ConversationEvents = {
  conversation_id: 'conv-123',
  items: [
    {
      sequence_no: 0,
      run_item_type: 'message',
      run_item_name: 'assistant',
      role: 'assistant',
      agent: 'triage',
      tool_call_id: null,
      tool_name: null,
      model: null,
      content_text: 'Hello from workflow',
      reasoning_text: null,
      call_arguments: null,
      call_output: null,
      attachments: [],
      response_id: 'resp-1',
      workflow_run_id: 'run-1',
      timestamp: new Date().toISOString(),
    },
  ],
};

describe('WorkflowRunConversation', () => {
  it('renders conversation events as transcript entries', () => {
    render(
      <WorkflowRunConversation
        run={run}
        events={events}
        isLoadingRun={false}
        isLoadingEvents={false}
      />,
    );

    expect(screen.getByText(/hello from workflow/i)).toBeInTheDocument();
    // Agent chip renders as "agent:triage" with no space; match flexibly
    expect(
      screen.getByText((content) => content.toLowerCase() === 'agent:triage'),
    ).toBeInTheDocument();
  });

  it('shows empty state when no run and no events', () => {
    render(
      <WorkflowRunConversation
        run={null}
        events={null}
        isLoadingRun={false}
        isLoadingEvents={false}
      />,
    );

    expect(screen.getByText(/select a run/i)).toBeInTheDocument();
  });
});
