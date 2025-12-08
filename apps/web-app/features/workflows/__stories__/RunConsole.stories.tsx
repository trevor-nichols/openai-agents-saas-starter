'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { RunConsole } from '../components/RunConsole';
import { mockWorkflowRunDetail, mockWorkflows } from '@/lib/workflows/mock';
import type { WorkflowSummaryView } from '@/lib/workflows/types';
import type { ConversationEvents } from '@/types/conversations';
import type { StreamingWorkflowEvent } from '@/lib/api/client/types.gen';

const streamEvents: (StreamingWorkflowEvent & { receivedAt: string })[] = [
  {
    workflow_key: 'triage-and-summary',
    workflow_run_id: 'run-stream-1',
    kind: 'lifecycle',
    event: 'run_started',
    sequence_number: 0,
    is_terminal: false,
    receivedAt: new Date().toISOString(),
  },
  {
    workflow_key: 'triage-and-summary',
    workflow_run_id: 'run-stream-1',
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
    workflow_key: 'triage-and-summary',
    workflow_run_id: 'run-stream-1',
    kind: 'raw_response_event',
    raw_type: 'response.completed',
    sequence_number: 2,
    is_terminal: true,
    text_delta: 'Done.',
    receivedAt: new Date().toISOString(),
  },
];

const runEvents: ConversationEvents = {
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
      content_text: 'Workflow response text.',
      reasoning_text: null,
      call_arguments: null,
      call_output: null,
      attachments: [],
      response_id: 'resp-1',
      workflow_run_id: 'run-stream-1',
      timestamp: new Date().toISOString(),
    },
  ],
};

const meta: Meta<typeof RunConsole> = {
  title: 'Workflows/Run Console',
  component: RunConsole,
};

export default meta;

type Story = StoryObj<typeof RunConsole>;

const defaultWorkflow: WorkflowSummaryView = {
  key: 'placeholder',
  display_name: 'Placeholder Workflow',
  description: 'Fallback workflow used for Storybook fixtures.',
  step_count: 1,
  default: false,
};

const [primaryWorkflow = defaultWorkflow] = mockWorkflows;
const runDetail = mockWorkflowRunDetail('run-stream-1');

export const Streaming: Story = {
  args: {
    workflows: mockWorkflows.length ? mockWorkflows : [primaryWorkflow],
    selectedWorkflowKey: primaryWorkflow.key,
    onRun: async (payload: { workflowKey: string; message: string }) => {
      console.log('run', payload);
    },
    isRunning: true,
    isLoadingWorkflows: false,
    runError: null,
    streamStatus: 'streaming',
    isMockMode: true,
    onSimulate: () => console.log('simulate stream'),
    streamEvents,
    lastRunSummary: { workflowKey: primaryWorkflow.key, runId: 'run-stream-1', message: 'Summarize customer issues' },
    lastUpdated: new Date().toISOString(),
    selectedRunId: 'run-stream-1',
    runDetail,
    runEvents,
    isLoadingRun: false,
    isLoadingEvents: false,
    onCancelRun: () => console.log('cancel run'),
    cancelPending: false,
    onDeleteRun: (runId) => console.log('delete', runId),
    deletingRunId: null,
  },
};

export const Completed: Story = {
  args: {
    workflows: mockWorkflows.length ? mockWorkflows : [primaryWorkflow],
    selectedWorkflowKey: primaryWorkflow.key,
    onRun: async (payload: { workflowKey: string; message: string }) => {
      console.log('run', payload);
    },
    isRunning: false,
    isLoadingWorkflows: false,
    runError: null,
    streamStatus: 'completed',
    isMockMode: false,
    onSimulate: undefined,
    streamEvents,
    lastRunSummary: { workflowKey: primaryWorkflow.key, runId: 'run-stream-1', message: 'Summarize customer issues' },
    lastUpdated: new Date().toISOString(),
    selectedRunId: 'run-stream-1',
    runDetail: { ...runDetail, status: 'succeeded' },
    runEvents,
    isLoadingRun: false,
    isLoadingEvents: false,
    onCancelRun: () => console.log('cancel run'),
    cancelPending: false,
    onDeleteRun: (runId) => console.log('delete', runId),
    deletingRunId: null,
  },
};

export const EmptyState: Story = {
  args: {
    workflows: mockWorkflows.length ? mockWorkflows : [primaryWorkflow],
    selectedWorkflowKey: null,
    onRun: async (payload: { workflowKey: string; message: string }) => {
      console.log('run', payload);
    },
    isRunning: false,
    isLoadingWorkflows: false,
    runError: null,
    streamStatus: 'idle',
    isMockMode: false,
    onSimulate: undefined,
    streamEvents: [],
    lastRunSummary: null,
    lastUpdated: null,
    selectedRunId: null,
    runDetail: null,
    runEvents: null,
    isLoadingRun: false,
    isLoadingEvents: false,
    onCancelRun: () => console.log('cancel run'),
    cancelPending: false,
    onDeleteRun: () => {},
    deletingRunId: null,
  },
};
