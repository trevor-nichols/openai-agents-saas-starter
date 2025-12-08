import type { Meta, StoryObj } from '@storybook/react';

import { WorkflowSidebar } from '../components/WorkflowSidebar';
import { mockWorkflowDescriptor, mockWorkflows } from '@/lib/workflows/mock';
import type { WorkflowSummaryView, WorkflowStageDescriptor } from '@/lib/workflows/types';

const defaultWorkflow: WorkflowSummaryView = {
  key: 'placeholder',
  display_name: 'Placeholder Workflow',
  description: 'Fallback workflow used for Storybook fixtures.',
  step_count: 1,
  default: false,
};

const [primaryWorkflow = defaultWorkflow] = mockWorkflows;
const descriptor = mockWorkflowDescriptor(primaryWorkflow.key);

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
    descriptor,
    isLoadingDescriptor: false,
  },
};

export const Loading: Story = {
  args: {
    workflows: [],
    isLoadingWorkflows: true,
    selectedKey: null,
    onSelect: () => {},
    descriptor: null,
    isLoadingDescriptor: true,
  },
};

export const WithActiveStep: Story = {
  args: {
    workflows: mockWorkflows,
    isLoadingWorkflows: false,
    selectedKey: primaryWorkflow.key,
    onSelect: (key) => console.log('select', key),
    descriptor: (() => {
      const extraStage: WorkflowStageDescriptor = {
        name: 'notify',
        mode: 'parallel',
        reducer: null,
        steps: [
          { name: 'Notify A', agent_key: 'agent-a', guard: null, guard_type: null, input_mapper: null, input_mapper_type: null, max_turns: null, output_schema: null },
          { name: 'Notify B', agent_key: 'agent-b', guard: null, guard_type: null, input_mapper: null, input_mapper_type: null, max_turns: null, output_schema: null },
        ],
      };
      return {
        ...descriptor,
        stages: [...(descriptor.stages ?? []), extraStage],
      };
    })(),
    isLoadingDescriptor: false,
    activeStep: { stageName: 'notify', parallelGroup: 'notify', branchIndex: 1 },
  },
};
