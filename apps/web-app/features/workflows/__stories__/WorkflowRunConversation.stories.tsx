import type { Meta, StoryObj } from '@storybook/react';

import { WorkflowRunConversation } from '../components/runs/transcript/WorkflowRunConversation';
import { mockWorkflowRunDetail } from '@/lib/workflows/mock';
import type { ConversationEvents } from '@/types/conversations';

const runDetail = mockWorkflowRunDetail('run-conversation');

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
      model: 'gpt-5.1',
      content_text: 'Hello from the workflow.',
      reasoning_text: null,
      call_arguments: null,
      call_output: null,
      attachments: [],
      response_id: 'resp-1',
      workflow_run_id: runDetail.workflow_run_id,
      timestamp: new Date().toISOString(),
    },
    {
      sequence_no: 1,
      run_item_type: 'message',
      run_item_name: 'assistant',
      role: 'assistant',
      agent: 'triage',
      tool_call_id: null,
      tool_name: null,
      model: 'gpt-5.1',
      content_text: 'Finished processing your request.',
      reasoning_text: null,
      call_arguments: null,
      call_output: { summary: 'All tasks completed.' },
      attachments: [],
      response_id: 'resp-2',
      workflow_run_id: runDetail.workflow_run_id,
      timestamp: new Date().toISOString(),
    },
  ],
};

const meta: Meta<typeof WorkflowRunConversation> = {
  title: 'Workflows/Workflow Run Conversation',
  component: WorkflowRunConversation,
};

export default meta;

type Story = StoryObj<typeof WorkflowRunConversation>;

export const WithEvents: Story = {
  args: {
    run: runDetail,
    events,
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
    events: null,
  },
};

export const Loading: Story = {
  args: {
    run: null,
    events: null,
    isLoadingRun: true,
    isLoadingEvents: true,
  },
};

export const NoRunSelected: Story = {
  args: {
    run: null,
    events: null,
  },
};
