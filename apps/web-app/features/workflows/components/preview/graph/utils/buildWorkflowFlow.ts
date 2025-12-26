import type { Edge } from '@xyflow/react';

import type { WorkflowDescriptor } from '@/lib/workflows/types';
import { workflowGraphNodeId } from '@/lib/workflows/streaming/graphNodeId';

import { WORKFLOW_GRAPH_COL_GAP_X, WORKFLOW_GRAPH_PARALLEL_ROW_GAP_Y } from '../constants';
import type { WorkflowAgentFlowNode } from '../nodes/WorkflowAgentNode';
import type { ResolvedActiveStep, WorkflowGraphNodeDataOptions } from '../types';

export type WorkflowGraphFlow = {
  nodes: WorkflowAgentFlowNode[];
  edges: Edge[];
};

export function buildWorkflowFlow(
  descriptor: WorkflowDescriptor | null,
  activeStep: ResolvedActiveStep | null,
  options: WorkflowGraphNodeDataOptions,
): WorkflowGraphFlow {
  if (!descriptor?.stages?.length) return { nodes: [], edges: [] };

  const {
    toolsByAgent = {},
    supportsContainersByAgent = {},
    supportsFileSearchByAgent = {},
    containers = [],
    containersError = null,
    isLoadingContainers = false,
    containerOverrides = {},
    onContainerOverrideChange,
    vectorStores = [],
    vectorStoresError = null,
    isLoadingVectorStores = false,
    vectorStoreOverrides = {},
    onVectorStoreOverrideChange,
  } = options;

  const activeNodeId = activeStep
    ? workflowGraphNodeId(activeStep.stageIndex, activeStep.stepIndex)
    : null;

  const stageSpans = descriptor.stages.map((stage) =>
    stage.mode === 'sequential' ? stage.steps.length : 1,
  );
  const stageStartCols: number[] = [];
  let cursor = 0;
  for (const span of stageSpans) {
    stageStartCols.push(cursor);
    cursor += span;
  }

  const nodes: WorkflowAgentFlowNode[] = [];
  const edges: Edge[] = [];

  descriptor.stages.forEach((stage, stageIndex) => {
    const startCol = stageStartCols[stageIndex] ?? 0;

    stage.steps.forEach((step, stepIndex) => {
      const col = stage.mode === 'sequential' ? startCol + stepIndex : startCol;
      const y =
        stage.mode === 'parallel'
          ? (stepIndex - (stage.steps.length - 1) / 2) * WORKFLOW_GRAPH_PARALLEL_ROW_GAP_Y
          : 0;

      const id = workflowGraphNodeId(stageIndex, stepIndex);
      const status = activeNodeId === id ? 'loading' : 'initial';
      const agentKey = step.agent_key;

      nodes.push({
        id,
        type: 'workflowAgent',
        position: { x: col * WORKFLOW_GRAPH_COL_GAP_X, y },
        data: {
          title: step.name,
          agentKey,
          stageName: stage.name,
          stageMode: stage.mode,
          status,
          tools: toolsByAgent[agentKey] ?? [],
          supportsContainers: Boolean(supportsContainersByAgent[agentKey]),
          supportsFileSearch: Boolean(supportsFileSearchByAgent[agentKey]),
          containers,
          containersError,
          isLoadingContainers,
          selectedContainerId: containerOverrides[agentKey] ?? null,
          onContainerOverrideChange,
          vectorStores,
          vectorStoresError,
          isLoadingVectorStores,
          selectedVectorStoreId: vectorStoreOverrides[agentKey] ?? null,
          onVectorStoreOverrideChange,
        },
      });

      if (stage.mode === 'sequential' && stepIndex > 0) {
        const source = workflowGraphNodeId(stageIndex, stepIndex - 1);
        const target = id;
        edges.push({
          id: `e:${source}->${target}`,
          source,
          target,
          animated: activeNodeId === target,
        });
      }
    });

    const nextStage = descriptor.stages[stageIndex + 1];
    if (!nextStage) return;

    const fromKeys =
      stage.mode === 'parallel'
        ? stage.steps.map((_, idx) => workflowGraphNodeId(stageIndex, idx))
        : [workflowGraphNodeId(stageIndex, stage.steps.length - 1)];

    const toKeys =
      nextStage.mode === 'parallel'
        ? nextStage.steps.map((_, idx) => workflowGraphNodeId(stageIndex + 1, idx))
        : [workflowGraphNodeId(stageIndex + 1, 0)];

    fromKeys.forEach((source) => {
      toKeys.forEach((target) => {
        edges.push({
          id: `e:${source}->${target}`,
          source,
          target,
          animated: activeNodeId === target,
        });
      });
    });
  });

  return { nodes, edges };
}
