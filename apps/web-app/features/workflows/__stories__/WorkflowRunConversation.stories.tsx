import type { Meta, StoryObj } from '@storybook/react';

import { WorkflowRunConversation } from '../components/runs/transcript/WorkflowRunConversation';
import { mockWorkflowRunDetail } from '@/lib/workflows/mock';
import type { PublicSseEvent } from '@/lib/api/client/types.gen';

const runDetail = mockWorkflowRunDetail('run-conversation');

const now = new Date().toISOString();
const replayEvents: PublicSseEvent[] = [
  {
    schema: 'public_sse_v1',
    kind: 'lifecycle',
    event_id: 1,
    stream_id: 'stream-story-replay',
    server_timestamp: now,
    conversation_id: runDetail.conversation_id ?? 'conv-123',
    response_id: 'resp-1',
    agent: 'triage',
    workflow: {
      workflow_key: runDetail.workflow_key,
      workflow_run_id: runDetail.workflow_run_id,
      stage_name: 'main',
      step_name: 'analyze',
      step_agent: 'triage',
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
    stream_id: 'stream-story-replay',
    server_timestamp: now,
    conversation_id: runDetail.conversation_id ?? 'conv-123',
    response_id: 'resp-1',
    agent: 'triage',
    workflow: {
      workflow_key: runDetail.workflow_key,
      workflow_run_id: runDetail.workflow_run_id,
      stage_name: 'main',
      step_name: 'analyze',
      step_agent: 'triage',
      parallel_group: null,
      branch_index: null,
    },
    output_index: 0,
    item_id: 'msg-story-1',
    content_index: 0,
    delta: 'Hello from the workflow.',
    provider_sequence_number: null,
    notices: null,
  },
  {
    schema: 'public_sse_v1',
    kind: 'message.delta',
    event_id: 3,
    stream_id: 'stream-story-replay',
    server_timestamp: now,
    conversation_id: runDetail.conversation_id ?? 'conv-123',
    response_id: 'resp-1',
    agent: 'triage',
    workflow: {
      workflow_key: runDetail.workflow_key,
      workflow_run_id: runDetail.workflow_run_id,
      stage_name: 'main',
      step_name: 'analyze',
      step_agent: 'triage',
      parallel_group: null,
      branch_index: null,
    },
    output_index: 0,
    item_id: 'msg-story-1',
    content_index: 0,
    delta: '\n\nFinished processing your request.',
    provider_sequence_number: null,
    notices: null,
  },
];

const meta: Meta<typeof WorkflowRunConversation> = {
  title: 'Workflows/Workflow Run Conversation',
  component: WorkflowRunConversation,
};

export default meta;

type Story = StoryObj<typeof WorkflowRunConversation>;

export const WithEvents: Story = {
  args: {
    run: runDetail,
    replayEvents,
  },
};

export const FromRunSteps: Story = {
  args: {
    run: {
      ...runDetail,
      steps: [
        ...runDetail.steps,
        {
          name: 'finalize',
          agent_key: 'analysis',
          response_text: 'Packaged the answer.',
          structured_output: { status: 'ok' },
          response_id: 'resp-3',
          stage_name: 'stage-2',
          parallel_group: null,
          branch_index: null,
          output_schema: { status: { type: 'string' } },
        },
      ],
    },
    replayEvents: null,
  },
};

export const Loading: Story = {
  args: {
    run: null,
    replayEvents: null,
    isLoadingRun: true,
    isLoadingReplay: true,
  },
};

export const NoRunSelected: Story = {
  args: {
    run: null,
    replayEvents: null,
  },
};
