import type { Meta, StoryObj } from '@storybook/react';

import { WorkflowStreamLog } from '../components/WorkflowStreamLog';
import type { StreamingWorkflowEvent } from '@/lib/api/client/types.gen';
import type { GeneratedImageFrame } from '@/lib/streams/imageFrames';

const now = new Date().toISOString();
const workflow = {
  workflow_key: 'triage-and-summary',
  workflow_run_id: 'run-stream-1',
  stage_name: 'main',
  step_name: 'analyze',
  step_agent: 'analysis',
  parallel_group: null,
  branch_index: null,
} as const;

const events: (StreamingWorkflowEvent & { receivedAt?: string })[] = [
  {
    schema: 'public_sse_v1',
    event_id: 1,
    stream_id: 'stream-story-workflow-log',
    server_timestamp: now,
    kind: 'lifecycle',
    conversation_id: 'conv-123',
    response_id: 'resp-1',
    agent: 'analysis',
    workflow,
    status: 'in_progress',
    receivedAt: now,
  },
  {
    schema: 'public_sse_v1',
    event_id: 2,
    stream_id: 'stream-story-workflow-log',
    server_timestamp: now,
    kind: 'message.delta',
    conversation_id: 'conv-123',
    response_id: 'resp-1',
    agent: 'analysis',
    workflow,
    output_index: 1,
    item_id: 'msg-1',
    content_index: 0,
    delta: 'Working on it...',
    receivedAt: now,
  },
  {
    schema: 'public_sse_v1',
    event_id: 3,
    stream_id: 'stream-story-workflow-log',
    server_timestamp: now,
    kind: 'tool.status',
    conversation_id: 'conv-123',
    response_id: 'resp-1',
    agent: 'analysis',
    workflow,
    output_index: 0,
    item_id: 'fs-1',
    tool: {
      tool_type: 'file_search',
      tool_call_id: 'fs-1',
      status: 'completed',
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
    receivedAt: now,
  },
  {
    schema: 'public_sse_v1',
    event_id: 4,
    stream_id: 'stream-story-workflow-log',
    server_timestamp: now,
    kind: 'tool.output',
    conversation_id: 'conv-123',
    response_id: 'resp-1',
    agent: 'analysis',
    workflow,
    output_index: 2,
    item_id: 'img-1',
    tool_call_id: 'img-1',
    tool_type: 'image_generation',
    output: [
      {
        id: 'img-1:0',
        status: 'completed',
        src: 'data:image/png;base64,aGVsbG8=',
        outputIndex: 0,
        revisedPrompt: 'Final frame',
      } satisfies GeneratedImageFrame,
    ],
    receivedAt: now,
  },
  {
    schema: 'public_sse_v1',
    event_id: 5,
    stream_id: 'stream-story-workflow-log',
    server_timestamp: now,
    kind: 'message.delta',
    conversation_id: 'conv-123',
    response_id: 'resp-1',
    agent: 'analysis',
    workflow,
    output_index: 1,
    item_id: 'msg-1',
    content_index: 0,
    delta: 'Done.',
    receivedAt: now,
  },
  {
    schema: 'public_sse_v1',
    event_id: 6,
    stream_id: 'stream-story-workflow-log',
    server_timestamp: now,
    kind: 'final',
    conversation_id: 'conv-123',
    response_id: 'resp-1',
    agent: 'analysis',
    workflow,
    final: {
      status: 'completed',
      response_text: 'Done.',
      structured_output: null,
      reasoning_summary_text: null,
      refusal_text: null,
      attachments: [],
      usage: { input_tokens: 1, output_tokens: 1, total_tokens: 2 },
    },
    receivedAt: now,
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
