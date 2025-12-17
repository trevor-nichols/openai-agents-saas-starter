import type { Meta, StoryObj } from '@storybook/react';

import { WorkflowList } from '../components/sidebar/WorkflowList';
import { mockWorkflows } from '@/lib/workflows/mock';
import type { WorkflowSummaryView } from '@/lib/workflows/types';

const defaultWorkflow: WorkflowSummaryView = {
  key: 'placeholder',
  display_name: 'Placeholder Workflow',
  description: 'Fallback workflow used for Storybook fixtures.',
  step_count: 1,
  default: false,
};

const [primaryWorkflow = defaultWorkflow, secondaryWorkflow = defaultWorkflow] = mockWorkflows;

const meta: Meta<typeof WorkflowList> = {
  title: 'Workflows/Workflow List',
  component: WorkflowList,
};

export default meta;

type Story = StoryObj<typeof WorkflowList>;

export const Default: Story = {
  args: {
    items: mockWorkflows,
    selectedKey: primaryWorkflow.key,
    onSelect: (key) => console.log('select', key),
  },
};

export const AlternateSelection: Story = {
  args: {
    items: mockWorkflows,
    selectedKey: secondaryWorkflow.key,
    onSelect: (key) => console.log('select', key),
  },
};

export const Loading: Story = {
  args: {
    items: [],
    isLoading: true,
    onSelect: () => {},
  },
};

export const Empty: Story = {
  args: {
    items: [],
    onSelect: () => {},
  },
};
