import type { Meta, StoryObj } from '@storybook/react';

import { WorkflowGraph } from '../components/WorkflowGraph';
import type { WorkflowDescriptor } from '@/lib/workflows/types';

const demoDescriptor: WorkflowDescriptor = {
  key: 'demo',
  display_name: 'Demo Workflow',
  description: 'Sequential collect stage followed by parallel notifications.',
  default: false,
  allow_handoff_agents: false,
  step_count: 4,
  output_schema: null,
  stages: [
    {
      name: 'collect',
      mode: 'sequential',
      reducer: null,
      steps: [
        { name: 'Collect Input', agent_key: 'agent-collect', guard: null, guard_type: null, input_mapper: null, input_mapper_type: null, max_turns: null, output_schema: null },
        { name: 'Summarize', agent_key: 'agent-summarize', guard: null, guard_type: null, input_mapper: null, input_mapper_type: null, max_turns: null, output_schema: null },
      ],
    },
    {
      name: 'notify',
      mode: 'parallel',
      reducer: null,
      steps: [
        { name: 'Notify A', agent_key: 'agent-a', guard: null, guard_type: null, input_mapper: null, input_mapper_type: null, max_turns: null, output_schema: null },
        { name: 'Notify B', agent_key: 'agent-b', guard: null, guard_type: null, input_mapper: null, input_mapper_type: null, max_turns: null, output_schema: null },
      ],
    },
  ],
};

const meta: Meta<typeof WorkflowGraph> = {
  title: 'Workflows/Workflow Graph',
  component: WorkflowGraph,
};

export default meta;

type Story = StoryObj<typeof WorkflowGraph>;

export const SequentialAndParallel: Story = {
  args: {
    descriptor: demoDescriptor,
  },
};

export const ActiveStepHighlighted: Story = {
  args: {
    descriptor: demoDescriptor,
    activeStep: { stepName: 'Notify A', stageName: 'notify', parallelGroup: 'notify', branchIndex: 0 },
  },
};

export const EmptyState: Story = {
  args: {
    descriptor: null,
  },
};
