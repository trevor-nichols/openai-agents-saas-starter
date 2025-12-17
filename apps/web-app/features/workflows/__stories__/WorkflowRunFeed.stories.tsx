'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { WorkflowRunFeed } from '../components/runs/WorkflowRunFeed';
import { mockWorkflowRunDetail, mockWorkflows } from '@/lib/workflows/mock';
import type { WorkflowSummaryView } from '@/lib/workflows/types';
import type { ConversationEvents } from '@/types/conversations';
import type { WorkflowStreamEventWithReceivedAt } from '../types';

const now = new Date().toISOString();
const workflowContext = {
  workflow_key: 'triage-and-summary',
  workflow_run_id: 'run-stream-1',
  stage_name: 'main',
  step_name: 'analyze',
  step_agent: 'analysis',
  parallel_group: null,
  branch_index: null,
} as const;

const streamEvents: WorkflowStreamEventWithReceivedAt[] = [
  {
    schema: 'public_sse_v1',
    event_id: 1,
    stream_id: 'stream-story-run-console',
    server_timestamp: now,
    kind: 'lifecycle',
    conversation_id: 'conv-123',
    response_id: 'resp-1',
    agent: 'analysis',
    workflow: workflowContext,
    status: 'in_progress',
    receivedAt: now,
  },
  {
    schema: 'public_sse_v1',
    event_id: 2,
    stream_id: 'stream-story-run-console',
    server_timestamp: now,
    kind: 'message.delta',
    conversation_id: 'conv-123',
    response_id: 'resp-1',
    agent: 'analysis',
    workflow: workflowContext,
    output_index: 0,
    item_id: 'msg-story-1',
    content_index: 0,
    delta: 'Working on it...',
    receivedAt: now,
  },
  {
    schema: 'public_sse_v1',
    event_id: 3,
    stream_id: 'stream-story-run-console',
    server_timestamp: now,
    kind: 'final',
    conversation_id: 'conv-123',
    response_id: 'resp-1',
    agent: 'analysis',
    workflow: workflowContext,
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

const meta: Meta<typeof WorkflowRunFeed> = {
  title: 'Workflows/Run Feed',
  component: WorkflowRunFeed,
};

export default meta;

type Story = StoryObj<typeof WorkflowRunFeed>;

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
    streamEvents,
    streamStatus: 'streaming',
    runError: null,
    isMockMode: true,
    onSimulate: () => console.log('simulate stream'),
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
    historyRuns: [],
    historyStatusFilter: 'all',
    onHistoryStatusChange: () => {},
    onHistoryRefresh: () => {},
    onHistoryLoadMore: undefined,
    historyHasMore: false,
    isHistoryLoading: false,
    isHistoryFetchingMore: false,
    onSelectRun: () => {},
  },
};

export const Completed: Story = {
  args: {
    workflows: mockWorkflows.length ? mockWorkflows : [primaryWorkflow],
    streamEvents,
    streamStatus: 'completed',
    runError: null,
    isMockMode: false,
    onSimulate: undefined,
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
    historyRuns: [],
    historyStatusFilter: 'all',
    onHistoryStatusChange: () => {},
    onHistoryRefresh: () => {},
    onHistoryLoadMore: undefined,
    historyHasMore: false,
    isHistoryLoading: false,
    isHistoryFetchingMore: false,
    onSelectRun: () => {},
  },
};

export const EmptyState: Story = {
  args: {
    workflows: mockWorkflows.length ? mockWorkflows : [primaryWorkflow],
    streamEvents: [],
    streamStatus: 'idle',
    runError: null,
    isMockMode: false,
    onSimulate: undefined,
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
    historyRuns: [],
    historyStatusFilter: 'all',
    onHistoryStatusChange: () => {},
    onHistoryRefresh: () => {},
    onHistoryLoadMore: undefined,
    historyHasMore: false,
    isHistoryLoading: false,
    isHistoryFetchingMore: false,
    onSelectRun: () => {},
  },
};
