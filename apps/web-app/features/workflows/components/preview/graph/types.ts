import type { ContainerResponse, VectorStoreResponse } from '@/lib/api/client/types.gen';
import type { WorkflowDescriptor } from '@/lib/workflows/types';
import type { WorkflowNodeStreamStore } from '@/lib/workflows/streaming';

export type WorkflowGraphActiveStep = {
  stepName?: string | null;
  stageName?: string | null;
  parallelGroup?: string | null;
  branchIndex?: number | null;
};

export type ResolvedActiveStep = {
  stageIndex: number;
  stepIndex: number;
};

export type WorkflowGraphNodeDataOptions = {
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
};

export type WorkflowGraphViewportProps = {
  descriptor: WorkflowDescriptor | null;
  nodeStreamStore?: WorkflowNodeStreamStore | null;
  activeStep?: WorkflowGraphActiveStep | null;
  className?: string;
} & WorkflowGraphNodeDataOptions;
