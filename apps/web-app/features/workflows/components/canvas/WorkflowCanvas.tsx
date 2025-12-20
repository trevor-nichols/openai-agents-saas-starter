'use client';

import type { LocationHint } from '@/lib/api/client/types.gen';
import type { ContainerResponse, VectorStoreResponse } from '@/lib/api/client/types.gen';
import type { WorkflowDescriptor } from '@/lib/workflows/types';
import type { WorkflowNodeStreamStore } from '@/lib/workflows/streaming';

import { WorkflowRunPanel } from './WorkflowRunPanel';
import { Separator } from '@/components/ui/separator';
import { WorkflowPreview } from '../preview/WorkflowPreview';

interface WorkflowCanvasProps {
  descriptor: WorkflowDescriptor | null;
  nodeStreamStore?: WorkflowNodeStreamStore | null;
  activeStep: {
    stepName: string | null;
    stageName: string | null;
    parallelGroup: string | null;
    branchIndex: number | null;
  } | null;
  toolsByAgent: Record<string, string[]>;
  supportsContainersByAgent: Record<string, boolean>;
  supportsFileSearchByAgent: Record<string, boolean>;
  containers: ContainerResponse[];
  containersError: string | null;
  isLoadingContainers: boolean;
  containerOverrides: Record<string, string | null>;
  onContainerOverrideChange: (agentKey: string, containerId: string | null) => void;
  vectorStores: VectorStoreResponse[];
  vectorStoresError: string | null;
  isLoadingVectorStores: boolean;
  vectorStoreOverrides: Record<string, string | null>;
  onVectorStoreOverrideChange: (agentKey: string, vectorStoreId: string | null) => void;
  selectedKey: string | null;
  onRun: (input: {
    workflowKey: string;
    message: string;
    shareLocation?: boolean;
    location?: LocationHint | null;
  }) => Promise<void>;
  isRunning: boolean;
  runError: string | null;
  isLoadingWorkflows: boolean;
  streamStatus?: 'idle' | 'connecting' | 'streaming' | 'completed' | 'error';
}

export function WorkflowCanvas({
  descriptor,
  nodeStreamStore,
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
  selectedKey,
  onRun,
  isRunning,
  runError,
  isLoadingWorkflows,
  streamStatus,
}: WorkflowCanvasProps) {
  return (
    <div className="flex h-full min-h-0 flex-col bg-muted/5">
      {/* Canvas Area */}
      <div className="flex-1 min-h-0 overflow-hidden relative">
        <div className="absolute inset-0">
          <WorkflowPreview
            descriptor={descriptor}
            nodeStreamStore={nodeStreamStore ?? null}
            activeStep={activeStep}
            toolsByAgent={toolsByAgent}
            supportsContainersByAgent={supportsContainersByAgent}
            supportsFileSearchByAgent={supportsFileSearchByAgent}
            containers={containers}
            containersError={containersError}
            isLoadingContainers={isLoadingContainers}
            containerOverrides={containerOverrides}
            onContainerOverrideChange={onContainerOverrideChange}
            vectorStores={vectorStores}
            vectorStoresError={vectorStoresError}
            isLoadingVectorStores={isLoadingVectorStores}
            vectorStoreOverrides={vectorStoreOverrides}
            onVectorStoreOverrideChange={onVectorStoreOverrideChange}
            className="h-full"
          />
        </div>
        
        {/* Dot pattern background effect */}
        <div className="absolute inset-0 -z-10 h-full w-full bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] [background-size:16px_16px] [mask-image:radial-gradient(ellipse_50%_50%_at_50%_50%,#000_70%,transparent_100%)] dark:bg-[radial-gradient(#1f2937_1px,transparent_1px)]" />
      </div>

      <Separator />

      {/* Configuration / Run Area */}
      <div className="flex-shrink-0 bg-background/50 backdrop-blur-sm p-6">
        <div className="mx-auto max-w-2xl">
            <WorkflowRunPanel
                selectedKey={selectedKey}
                onRun={onRun}
                isRunning={isRunning}
                runError={runError}
                isLoadingWorkflows={isLoadingWorkflows}
                streamStatus={streamStatus}
            />
        </div>
      </div>
    </div>
  );
}
