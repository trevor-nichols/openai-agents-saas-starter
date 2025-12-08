import type { Meta, StoryObj } from '@storybook/react';

import { RunHistoryPanel } from '../components/RunHistoryPanel';
import { mockWorkflowRunList, mockWorkflows } from '@/lib/workflows/mock';
import type { WorkflowStatusFilter } from '../constants';
import type { WorkflowSummaryView, WorkflowRunListItemView } from '@/lib/workflows/types';

const runs = mockWorkflowRunList().items;
const primaryRun: WorkflowRunListItemView =
  runs[0] ??
  ({
    workflow_run_id: 'run-placeholder',
    workflow_key: 'triage-and-summary',
    status: 'succeeded',
    started_at: new Date().toISOString(),
    ended_at: new Date().toISOString(),
    user_id: 'user-placeholder',
    conversation_id: 'conv-placeholder',
    step_count: 1,
    duration_ms: 1000,
    final_output_text: 'Placeholder run',
  } as WorkflowRunListItemView);

const defaultWorkflow: WorkflowSummaryView = {
  key: 'placeholder',
  display_name: 'Placeholder Workflow',
  description: 'Fallback workflow used for Storybook fixtures.',
  step_count: 1,
  default: false,
};

const [primaryWorkflow = defaultWorkflow] = mockWorkflows;

const meta: Meta<typeof RunHistoryPanel> = {
  title: 'Workflows/Run History Panel',
  component: RunHistoryPanel,
};

export default meta;

type Story = StoryObj<typeof RunHistoryPanel>;

const baseArgs = {
  workflows: mockWorkflows.length ? mockWorkflows : [primaryWorkflow],
  statusFilter: 'all' as WorkflowStatusFilter,
  onStatusChange: (value: WorkflowStatusFilter) => console.log('filter', value),
  onRefresh: () => console.log('refresh'),
  onLoadMore: () => console.log('load more'),
  hasMore: true,
  isLoading: false,
  isFetchingMore: false,
  onSelectRun: (runId: string) => console.log('select', runId),
  selectedRunId: null,
  onDeleteRun: (runId: string) => console.log('delete', runId),
  deletingRunId: null,
};

export const Default: Story = {
  args: {
    ...baseArgs,
    runs,
  },
};

export const WithSelection: Story = {
  args: {
    ...baseArgs,
    runs,
    selectedRunId: primaryRun.workflow_run_id,
  },
};

export const Loading: Story = {
  args: {
    ...baseArgs,
    runs: [],
    isLoading: true,
  },
};

export const Empty: Story = {
  args: {
    ...baseArgs,
    runs: [],
    hasMore: false,
  },
};
