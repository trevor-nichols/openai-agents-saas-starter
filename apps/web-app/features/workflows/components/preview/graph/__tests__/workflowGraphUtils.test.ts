import { describe, expect, it } from 'vitest';

import type { WorkflowDescriptor } from '@/lib/workflows/types';
import { workflowGraphNodeId } from '@/lib/workflows/streaming/graphNodeId';

import { buildWorkflowFlow } from '../utils/buildWorkflowFlow';
import { resolveActiveStep } from '../utils/resolveActiveStep';

const descriptor: WorkflowDescriptor = {
  key: 'demo',
  display_name: 'Demo Workflow',
  description: 'Demo',
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

describe('workflow graph utils', () => {
  it('resolves active step by step name', () => {
    const resolved = resolveActiveStep(descriptor, {
      stepName: 'Summarize',
      stageName: null,
      parallelGroup: null,
      branchIndex: null,
    });

    expect(resolved).toEqual({ stageIndex: 0, stepIndex: 1 });
  });

  it('resolves active step by parallel group and branch', () => {
    const resolved = resolveActiveStep(descriptor, {
      stepName: null,
      stageName: null,
      parallelGroup: 'notify',
      branchIndex: 1,
    });

    expect(resolved).toEqual({ stageIndex: 1, stepIndex: 1 });
  });

  it('builds graph nodes and edges with active status', () => {
    const flow = buildWorkflowFlow(descriptor, { stageIndex: 1, stepIndex: 0 }, {});

    expect(flow.nodes).toHaveLength(4);
    expect(flow.edges).toHaveLength(3);

    const activeNode = flow.nodes.find((node) => node.id === workflowGraphNodeId(1, 0));
    const inactiveNode = flow.nodes.find((node) => node.id === workflowGraphNodeId(0, 0));

    expect(activeNode?.data.status).toBe('loading');
    expect(inactiveNode?.data.status).toBe('initial');

    const edgeIds = flow.edges.map((edge) => edge.id);
    expect(edgeIds).toContain(`e:${workflowGraphNodeId(0, 0)}->${workflowGraphNodeId(0, 1)}`);
    expect(edgeIds).toContain(`e:${workflowGraphNodeId(0, 1)}->${workflowGraphNodeId(1, 0)}`);
    expect(edgeIds).toContain(`e:${workflowGraphNodeId(0, 1)}->${workflowGraphNodeId(1, 1)}`);
  });
});
