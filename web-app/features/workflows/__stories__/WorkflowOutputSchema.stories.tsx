import type { Meta, StoryObj } from '@storybook/react';

import { WorkflowDescriptorCard } from '../components/WorkflowDescriptorCard';
import { WorkflowRunDetail } from '../components/WorkflowRunDetail';
import { mockWorkflowDescriptor, mockWorkflowRunDetail } from '@/lib/workflows/mock';

const descriptor = mockWorkflowDescriptor('triage-and-summary');
const runDetail = mockWorkflowRunDetail('run-preview');

const Showcase = () => (
  <div className="space-y-6 max-w-4xl">
    <WorkflowDescriptorCard descriptor={descriptor} />
    <WorkflowRunDetail run={runDetail} />
  </div>
);

const meta: Meta<typeof Showcase> = {
  title: 'Workflows/Output Schema',
  component: Showcase,
};

export default meta;

type Story = StoryObj<typeof Showcase>;

export const Default: Story = {};
