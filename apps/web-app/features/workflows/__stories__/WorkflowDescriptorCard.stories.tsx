import type { Meta, StoryObj } from '@storybook/react';

import { WorkflowDescriptorCard } from '../components/preview/outline/WorkflowDescriptorCard';
import { mockWorkflowDescriptor } from '@/lib/workflows/mock';

const descriptor = mockWorkflowDescriptor('triage-and-summary');

const meta: Meta<typeof WorkflowDescriptorCard> = {
  title: 'Workflows/Workflow Descriptor Card',
  component: WorkflowDescriptorCard,
};

export default meta;

type Story = StoryObj<typeof WorkflowDescriptorCard>;

export const Default: Story = {
  args: {
    descriptor,
  },
};

export const WithHandoffsEnabled: Story = {
  args: {
    descriptor: { ...descriptor, allow_handoff_agents: true },
  },
};

export const Loading: Story = {
  args: {
    descriptor: null,
    isLoading: true,
  },
};

export const Empty: Story = {
  args: {
    descriptor: null,
  },
};
