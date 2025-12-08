import type { Meta, StoryObj } from '@storybook/react';

import { WorkflowRunsTable } from '../components/WorkflowRunsTable';
import { mockWorkflowRunList } from '@/lib/workflows/mock';
import type { WorkflowRunListItemView } from '@/lib/workflows/types';

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

const meta: Meta<typeof WorkflowRunsTable> = {
  title: 'Workflows/Workflow Runs Table',
  component: WorkflowRunsTable,
};

export default meta;

type Story = StoryObj<typeof WorkflowRunsTable>;

export const Default: Story = {
  args: {
    runs,
    onSelectRun: (runId) => console.log('select', runId),
  },
};

export const WithSelectedRow: Story = {
  args: {
    runs,
    selectedRunId: primaryRun.workflow_run_id,
    onSelectRun: (runId) => console.log('select', runId),
  },
};

export const WithLoadMore: Story = {
  args: {
    runs,
    hasMore: true,
    isFetchingMore: false,
    onLoadMore: () => console.log('load more'),
    onSelectRun: (runId) => console.log('select', runId),
  },
};

export const Loading: Story = {
  args: {
    runs: [],
    isLoading: true,
    onSelectRun: () => {},
  },
};

export const EmptyState: Story = {
  args: {
    runs: [],
    onSelectRun: () => {},
    onRefresh: () => console.log('refresh'),
  },
};
