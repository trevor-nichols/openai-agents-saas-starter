'use client';

import { useMemo } from 'react';
import {
  Background,
  Controls,
  ReactFlow,
  ReactFlowProvider,
  type NodeTypes,
} from '@xyflow/react';

import { cn } from '@/lib/utils';

import { WORKFLOW_GRAPH_BACKGROUND, WORKFLOW_GRAPH_DEFAULT_EDGE_OPTIONS } from './constants';
import { useFitViewOnNodes } from './hooks/useFitViewOnNodes';
import { useWorkflowGraphFlow } from './hooks/useWorkflowGraphFlow';
import { WorkflowGraphEmptyState } from './WorkflowGraphEmptyState';
import { WorkflowAgentNode } from './nodes/WorkflowAgentNode';
import { WorkflowNodeStreamProvider } from './nodeStreamContext';
import type { WorkflowGraphViewportProps } from './types';

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
  const nodeDataOptions = useMemo(
    () => ({
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

  const { flow } = useWorkflowGraphFlow(descriptor, activeStep, nodeDataOptions);

  useFitViewOnNodes(flow.nodes.length, descriptor?.key ?? null);

  if (!descriptor) {
    return <WorkflowGraphEmptyState variant="centered" className={className} />;
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
        defaultEdgeOptions={WORKFLOW_GRAPH_DEFAULT_EDGE_OPTIONS}
      >
        <Controls className="bg-background/60" />
        <Background {...WORKFLOW_GRAPH_BACKGROUND} />
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
