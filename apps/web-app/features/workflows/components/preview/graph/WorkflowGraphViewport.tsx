'use client';

import { useEffect, useMemo } from 'react';
import {
  Background,
  BackgroundVariant,
  Controls,
  MarkerType,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
  type Edge,
  type NodeTypes,
} from '@xyflow/react';

import { cn } from '@/lib/utils';
import type { ContainerResponse, VectorStoreResponse } from '@/lib/api/client/types.gen';
import type { WorkflowDescriptor } from '@/lib/workflows/types';
import type { WorkflowNodeStreamStore } from '@/lib/workflows/streaming';

import {
  WorkflowAgentNode,
  type WorkflowAgentFlowNode,
} from './nodes/WorkflowAgentNode';
import { WorkflowNodeStreamProvider } from './nodeStreamContext';

interface WorkflowGraphViewportProps {
  descriptor: WorkflowDescriptor | null;
  nodeStreamStore?: WorkflowNodeStreamStore | null;
  activeStep?: {
    stepName?: string | null;
    stageName?: string | null;
    parallelGroup?: string | null;
    branchIndex?: number | null;
  } | null;
  toolsByAgent?: Record<string, string[]>;
  supportsContainersByAgent?: Record<string, boolean>;
  supportsFileSearchByAgent?: Record<string, boolean>;
  containers?: ContainerResponse[];
  containersError?: string | null;
  isLoadingContainers?: boolean;
  containerOverrides?: Record<string, string | null>;
  onContainerOverrideChange?: (agentKey: string, containerId: string | null) => void;
  vectorStores?: VectorStoreResponse[];
  vectorStoresError?: string | null;
  isLoadingVectorStores?: boolean;
  vectorStoreOverrides?: Record<string, string | null>;
  onVectorStoreOverrideChange?: (agentKey: string, vectorStoreId: string | null) => void;
  className?: string;
}

type WorkflowStepKey = `${number}:${number}`;

const NODE_WIDTH = 360;
const NODE_COL_PADDING = 80;
const COL_GAP_X = NODE_WIDTH + NODE_COL_PADDING;
const NODE_HEIGHT_ESTIMATE = 210;
const PARALLEL_ROW_PADDING = 72;
const PARALLEL_ROW_GAP_Y = NODE_HEIGHT_ESTIMATE + PARALLEL_ROW_PADDING;

function stepKey(stageIndex: number, stepIndex: number): WorkflowStepKey {
  return `${stageIndex}:${stepIndex}`;
}

function computeActiveStepKey(descriptor: WorkflowDescriptor | null, activeStep: WorkflowGraphViewportProps['activeStep']) {
  if (!descriptor?.stages?.length || !activeStep) return null;

  const match = descriptor.stages.flatMap((stage, stageIndex) =>
    stage.steps.map((step, stepIndex) => ({
      stage,
      stageIndex,
      step,
      stepIndex,
      key: stepKey(stageIndex, stepIndex),
    })),
  ).find((candidate) => {
    const branchMatches = activeStep.branchIndex == null || activeStep.branchIndex === candidate.stepIndex;
    if (activeStep.stepName) {
      return candidate.step.name === activeStep.stepName && branchMatches;
    }
    if (activeStep.stageName) {
      return candidate.stage.name === activeStep.stageName && branchMatches;
    }
    if (activeStep.parallelGroup) {
      return candidate.stage.name === activeStep.parallelGroup && branchMatches;
    }
    return false;
  });

  return match?.key ?? null;
}

function buildFlow(
  descriptor: WorkflowDescriptor | null,
  activeKey: WorkflowStepKey | null,
  options: {
    toolsByAgent?: Record<string, string[]>;
    supportsContainersByAgent?: Record<string, boolean>;
    supportsFileSearchByAgent?: Record<string, boolean>;
    containers?: ContainerResponse[];
    containersError?: string | null;
    isLoadingContainers?: boolean;
    containerOverrides?: Record<string, string | null>;
    onContainerOverrideChange?: (agentKey: string, containerId: string | null) => void;
    vectorStores?: VectorStoreResponse[];
    vectorStoresError?: string | null;
    isLoadingVectorStores?: boolean;
    vectorStoreOverrides?: Record<string, string | null>;
    onVectorStoreOverrideChange?: (agentKey: string, vectorStoreId: string | null) => void;
  },
) {
  if (!descriptor?.stages?.length) return { nodes: [] as WorkflowAgentFlowNode[], edges: [] as Edge[] };

  const stageSpans = descriptor.stages.map((stage) => (stage.mode === 'sequential' ? stage.steps.length : 1));
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
          ? (stepIndex - (stage.steps.length - 1) / 2) * PARALLEL_ROW_GAP_Y
          : 0;

      const id = stepKey(stageIndex, stepIndex);
      const status = activeKey === id ? 'loading' : 'initial';

      nodes.push({
        id,
        type: 'workflowAgent',
        position: { x: col * COL_GAP_X, y },
        data: {
          title: step.name,
          agentKey: step.agent_key,
          stageName: stage.name,
          stageMode: stage.mode,
          status,
          tools: options.toolsByAgent?.[step.agent_key] ?? [],
          supportsContainers: Boolean(options.supportsContainersByAgent?.[step.agent_key]),
          supportsFileSearch: Boolean(options.supportsFileSearchByAgent?.[step.agent_key]),
          containers: options.containers ?? [],
          containersError: options.containersError ?? null,
          isLoadingContainers: Boolean(options.isLoadingContainers),
          selectedContainerId: options.containerOverrides?.[step.agent_key] ?? null,
          onContainerOverrideChange: options.onContainerOverrideChange,
          vectorStores: options.vectorStores ?? [],
          vectorStoresError: options.vectorStoresError ?? null,
          isLoadingVectorStores: Boolean(options.isLoadingVectorStores),
          selectedVectorStoreId: options.vectorStoreOverrides?.[step.agent_key] ?? null,
          onVectorStoreOverrideChange: options.onVectorStoreOverrideChange,
        },
      });

      if (stage.mode === 'sequential' && stepIndex > 0) {
        const source = stepKey(stageIndex, stepIndex - 1);
        const target = id;
        edges.push({
          id: `e:${source}->${target}`,
          source,
          target,
          animated: activeKey === target,
        });
      }
    });

    const nextStage = descriptor.stages[stageIndex + 1];
    if (!nextStage) return;

    const fromKeys =
      stage.mode === 'parallel'
        ? stage.steps.map((_, idx) => stepKey(stageIndex, idx))
        : [stepKey(stageIndex, stage.steps.length - 1)];

    const toKeys =
      nextStage.mode === 'parallel'
        ? nextStage.steps.map((_, idx) => stepKey(stageIndex + 1, idx))
        : [stepKey(stageIndex + 1, 0)];

    fromKeys.forEach((source) => {
      toKeys.forEach((target) => {
        edges.push({
          id: `e:${source}->${target}`,
          source,
          target,
          animated: activeKey === target,
        });
      });
    });
  });

  return { nodes, edges };
}

const nodeTypes: NodeTypes = {
  workflowAgent: WorkflowAgentNode,
};

function WorkflowGraphViewportInner({
  descriptor,
  activeStep,
  toolsByAgent,
  supportsContainersByAgent,
  supportsFileSearchByAgent,
  containers,
  containersError,
  isLoadingContainers,
  containerOverrides,
  onContainerOverrideChange,
  vectorStores,
  vectorStoresError,
  isLoadingVectorStores,
  vectorStoreOverrides,
  onVectorStoreOverrideChange,
  className,
}: WorkflowGraphViewportProps) {
  const activeKey = useMemo(() => computeActiveStepKey(descriptor, activeStep), [descriptor, activeStep]);
  const flow = useMemo(
    () =>
      buildFlow(descriptor, activeKey, {
        toolsByAgent,
        supportsContainersByAgent,
        supportsFileSearchByAgent,
        containers,
        containersError,
        isLoadingContainers,
        containerOverrides,
        onContainerOverrideChange,
        vectorStores,
        vectorStoresError,
        isLoadingVectorStores,
        vectorStoreOverrides,
        onVectorStoreOverrideChange,
      }),
    [
      descriptor,
      activeKey,
      toolsByAgent,
      supportsContainersByAgent,
      supportsFileSearchByAgent,
      containers,
      containersError,
      isLoadingContainers,
      containerOverrides,
      onContainerOverrideChange,
      vectorStores,
      vectorStoresError,
      isLoadingVectorStores,
      vectorStoreOverrides,
      onVectorStoreOverrideChange,
    ],
  );
  const { fitView } = useReactFlow();

  useEffect(() => {
    if (!flow.nodes.length) return;
    const handle = requestAnimationFrame(() => {
      fitView({ padding: 0.2, duration: 200 });
    });
    return () => cancelAnimationFrame(handle);
  }, [descriptor?.key, fitView, flow.nodes.length]);

  if (!descriptor) {
    return (
      <div className={cn('flex h-full w-full items-center justify-center p-6', className)}>
        <div className="rounded-lg border border-white/5 bg-white/5 p-4">
          <p className="text-sm text-foreground/70">Select a workflow to preview its structure.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('h-full w-full', className)}>
      <ReactFlow
        nodes={flow.nodes}
        edges={flow.edges}
        nodeTypes={nodeTypes}
        fitView
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable
        className="bg-transparent"
        defaultEdgeOptions={{
          type: 'smoothstep',
          markerEnd: { type: MarkerType.ArrowClosed },
          style: {
            strokeWidth: 2,
          },
        }}
      >
        <Controls className="bg-background/60" />
        <Background
          variant={BackgroundVariant.Dots}
          gap={24}
          size={1}
          color="hsl(var(--border))"
          className="opacity-60"
        />
      </ReactFlow>
    </div>
  );
}

export function WorkflowGraphViewport(props: WorkflowGraphViewportProps) {
  return (
    <WorkflowNodeStreamProvider store={props.nodeStreamStore ?? null}>
      <ReactFlowProvider>
        <WorkflowGraphViewportInner {...props} />
      </ReactFlowProvider>
    </WorkflowNodeStreamProvider>
  );
}
