'use client';

import type { WorkflowDescriptorResponse, LocationHint } from '@/lib/api/client/types.gen';

import { WorkflowGraph } from './WorkflowGraph';
import { WorkflowRunPanel } from './WorkflowRunPanel';
import { Separator } from '@/components/ui/separator';

interface WorkflowCanvasProps {
  descriptor: WorkflowDescriptorResponse | null;
  activeStep: {
    stageName: string | null;
    parallelGroup: string | null;
    branchIndex: number | null;
  } | null;
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
  activeStep,
  selectedKey,
  onRun,
  isRunning,
  runError,
  isLoadingWorkflows,
  streamStatus,
}: WorkflowCanvasProps) {
  return (
    <div className="flex h-full flex-col bg-muted/5">
      {/* Canvas Area */}
      <div className="flex-1 overflow-hidden relative">
        <div className="absolute inset-0 flex items-center justify-center p-8">
            <WorkflowGraph 
                descriptor={descriptor} 
                activeStep={activeStep} 
                className="w-full max-w-4xl h-full border-none bg-transparent shadow-none" 
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
