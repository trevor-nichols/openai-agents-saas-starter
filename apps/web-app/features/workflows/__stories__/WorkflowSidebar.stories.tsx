import type { Meta, StoryObj } from '@storybook/react';

import { WorkflowSidebar } from '../components/WorkflowSidebar';
import { mockWorkflows } from '@/lib/workflows/mock';
import type { WorkflowSummaryView } from '@/lib/workflows/types';

const defaultWorkflow: WorkflowSummaryView = {
  key: 'placeholder',
  display_name: 'Placeholder Workflow',
  description: 'Fallback workflow used for Storybook fixtures.',
  step_count: 1,
  default: false,
};

const [primaryWorkflow = defaultWorkflow] = mockWorkflows;

const meta: Meta<typeof WorkflowSidebar> = {
  title: 'Workflows/Workflow Sidebar',
  component: WorkflowSidebar,
};

export default meta;

type Story = StoryObj<typeof WorkflowSidebar>;

export const Default: Story = {
  args: {
    workflows: mockWorkflows,
    isLoadingWorkflows: false,
    selectedKey: primaryWorkflow.key,
    onSelect: (key) => console.log('select', key),
  },
};

export const Loading: Story = {
  args: {
    workflows: [],
    isLoadingWorkflows: true,
    selectedKey: null,
    onSelect: () => {},
  },
};

export const WithActiveStep: Story = {
  args: {
    workflows: mockWorkflows,
    isLoadingWorkflows: false,
    selectedKey: primaryWorkflow.key,
    onSelect: (key) => console.log('select', key),
  },
};
