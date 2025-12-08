import type { Meta, StoryObj } from '@storybook/react';

import { WorkflowStreamLog } from '../components/WorkflowStreamLog';
import type { StreamingWorkflowEvent } from '@/lib/api/client/types.gen';

const base = {
  workflow_key: 'triage-and-summary',
  workflow_run_id: 'run-stream-1',
};

const events: (StreamingWorkflowEvent & { receivedAt?: string })[] = [
  {
    ...base,
    kind: 'lifecycle',
    event: 'run_started',
    is_terminal: false,
    sequence_number: 0,
    receivedAt: new Date().toISOString(),
  },
  {
    ...base,
    kind: 'run_item_stream_event',
    event: 'agent_output',
    sequence_number: 1,
    run_item_name: 'agent_output',
    run_item_type: 'agent',
    agent: 'researcher',
    response_text: 'Working on it...',
    structured_output: null,
    is_terminal: false,
    receivedAt: new Date().toISOString(),
  },
  {
    ...base,
    kind: 'run_item_stream_event',
    event: 'tool_call',
    sequence_number: 2,
    tool_call: {
      tool_type: 'file_search',
      file_search_call: {
        id: 'fs-1',
        type: 'file_search_call',
        status: 'searching',
        queries: ['report'],
        results: [
          {
            file_id: 'file-1',
            filename: 'report.pdf',
            score: 0.91,
            vector_store_id: 'vs-1',
            text: 'Quarterly summary',
          },
        ],
      },
    },
    is_terminal: false,
    receivedAt: new Date().toISOString(),
  },
  {
    ...base,
    kind: 'run_item_stream_event',
    event: 'tool_call',
    sequence_number: 3,
    tool_call: {
      tool_type: 'image_generation',
      image_generation_call: {
        id: 'img-1',
        type: 'image_generation_call',
        status: 'partial_image',
        result: 'data:image/png;base64,aGVsbG8=',
        format: 'png',
      },
    },
    is_terminal: false,
    receivedAt: new Date().toISOString(),
  },
  {
    ...base,
    kind: 'raw_response_event',
    raw_type: 'response.output_text.delta',
    text_delta: 'Done.',
    sequence_number: 4,
    is_terminal: false,
    receivedAt: new Date().toISOString(),
  },
  {
    ...base,
    kind: 'raw_response_event',
    raw_type: 'response.completed',
    text_delta: '',
    sequence_number: 5,
    is_terminal: true,
    receivedAt: new Date().toISOString(),
  },
];

const meta: Meta<typeof WorkflowStreamLog> = {
  title: 'Workflows/Workflow Stream Log',
  component: WorkflowStreamLog,
};

export default meta;

type Story = StoryObj<typeof WorkflowStreamLog>;

export const MixedEvents: Story = {
  args: {
    events,
  },
};

export const Empty: Story = {
  args: {
    events: [],
  },
};
