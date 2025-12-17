'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { WorkflowCanvas, WorkflowRunFeed, WorkflowSidebar } from '../components';
import { mockWorkflowDescriptor, mockWorkflowRunDetail, mockWorkflowRunList, mockWorkflows } from '@/lib/workflows/mock';
import type {
  WorkflowSummaryView,
  WorkflowRunListItemView,
} from '@/lib/workflows/types';
import type { ConversationEvents } from '@/types/conversations';
import type { StreamStatus } from '../constants';
import type { WorkflowStreamEventWithReceivedAt } from '../types';

const defaultWorkflow: WorkflowSummaryView = {
  key: 'placeholder',
  display_name: 'Placeholder Workflow',
  description: 'Fallback workflow used for Storybook fixtures.',
  step_count: 1,
  default: false,
};

const workflows = mockWorkflows.length ? mockWorkflows : [defaultWorkflow];
const primaryWorkflow = workflows[0] ?? defaultWorkflow;

const runs = mockWorkflowRunList().items;
const primaryRun: WorkflowRunListItemView =
  runs[0] ??
  ({
    workflow_run_id: 'run-placeholder',
    workflow_key: primaryWorkflow.key,
    status: 'succeeded',
    started_at: new Date().toISOString(),
    ended_at: new Date().toISOString(),
    user_id: 'user-placeholder',
    conversation_id: 'conv-placeholder',
    step_count: 1,
    duration_ms: 1000,
    final_output_text: 'Placeholder run',
  } as WorkflowRunListItemView);

const runDetail = mockWorkflowRunDetail('run-story');

const now = new Date().toISOString();
const workflowContext = {
  workflow_key: runDetail.workflow_key,
  workflow_run_id: runDetail.workflow_run_id,
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
    stream_id: 'stream-story-workflows-page',
    server_timestamp: now,
    kind: 'lifecycle',
    conversation_id: runDetail.conversation_id ?? 'conv-story',
    response_id: 'resp-1',
    agent: 'analysis',
    workflow: workflowContext,
    status: 'in_progress',
    receivedAt: now,
  },
  {
    schema: 'public_sse_v1',
    event_id: 2,
    stream_id: 'stream-story-workflows-page',
    server_timestamp: now,
    kind: 'message.delta',
    conversation_id: runDetail.conversation_id ?? 'conv-story',
    response_id: 'resp-1',
    agent: 'analysis',
    workflow: workflowContext,
    output_index: 0,
    item_id: 'msg-1',
    content_index: 0,
    delta: 'Working on it...',
    receivedAt: now,
  },
  {
    schema: 'public_sse_v1',
    event_id: 3,
    stream_id: 'stream-story-workflows-page',
    server_timestamp: now,
    kind: 'final',
    conversation_id: runDetail.conversation_id ?? 'conv-story',
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
  conversation_id: runDetail.conversation_id ?? 'conv-story',
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
      workflow_run_id: runDetail.workflow_run_id,
      timestamp: new Date().toISOString(),
    },
  ],
};

type WorkspacePreviewProps = {
  streamStatus: StreamStatus;
  isRunning: boolean;
  runError?: string | null;
};

function WorkspacePreview({ streamStatus, isRunning, runError = null }: WorkspacePreviewProps) {
  const descriptor = mockWorkflowDescriptor(primaryWorkflow.key);
  const activeStep = {
    stageName: workflowContext.stage_name,
    parallelGroup: workflowContext.parallel_group,
    branchIndex: workflowContext.branch_index,
  };

  return (
    <div className="grid min-h-[700px] gap-4 lg:grid-cols-[320px_minmax(0,1fr)_380px]">
      <div className="min-h-0">
        <WorkflowSidebar
          workflows={workflows}
          isLoadingWorkflows={false}
          selectedKey={primaryWorkflow.key}
          onSelect={(key) => console.log('select', key)}
        />
      </div>

      <div className="min-h-0 overflow-hidden rounded-lg border border-white/5">
        <WorkflowCanvas
          descriptor={descriptor}
          activeStep={activeStep}
          selectedKey={primaryWorkflow.key}
          onRun={async (payload) => {
            console.log('run', payload);
          }}
          isRunning={isRunning}
          isLoadingWorkflows={false}
          runError={runError}
          streamStatus={streamStatus}
        />
      </div>

      <div className="min-h-0 overflow-hidden rounded-lg border border-white/5">
        <WorkflowRunFeed
          workflows={workflows}
          streamEvents={streamEvents}
          streamStatus={streamStatus}
          runError={runError}
          isMockMode={false}
          onSimulate={undefined}
          lastRunSummary={{
            workflowKey: primaryWorkflow.key,
            runId: runDetail.workflow_run_id,
            message: 'Summarize customer issues',
          }}
          lastUpdated={new Date().toISOString()}
          selectedRunId={runDetail.workflow_run_id}
          runDetail={runDetail}
          runEvents={runEvents}
          isLoadingRun={false}
          isLoadingEvents={false}
          onCancelRun={() => console.log('cancel run')}
          cancelPending={false}
          onDeleteRun={(runId) => console.log('delete', runId)}
          deletingRunId={null}
          historyRuns={runs.length ? runs : [primaryRun]}
          historyStatusFilter="all"
          onHistoryStatusChange={(status) => console.log('filter', status)}
          onHistoryRefresh={() => console.log('refresh')}
          onHistoryLoadMore={() => console.log('load more')}
          historyHasMore={false}
          isHistoryLoading={false}
          isHistoryFetchingMore={false}
          onSelectRun={(runId) => console.log('select', runId)}
        />
      </div>
    </div>
  );
}

const meta: Meta<typeof WorkspacePreview> = {
  title: 'Workflows/Page',
  component: WorkspacePreview,
};

export default meta;

type Story = StoryObj<typeof WorkspacePreview>;

export const Streaming: Story = {
  args: {
    streamStatus: 'streaming',
    isRunning: true,
  },
};

export const Completed: Story = {
  args: {
    streamStatus: 'completed',
    isRunning: false,
  },
};

export const ErrorState: Story = {
  args: {
    streamStatus: 'error',
    isRunning: false,
    runError: 'Workflow run ended with an error.',
  },
};
