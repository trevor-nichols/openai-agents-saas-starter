'use client';

import { LayoutGrid, List } from 'lucide-react';

import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';
import type { WorkflowDescriptor } from '@/lib/workflows/types';

import type { WorkflowPreviewMode } from '../../hooks/useWorkflowPreviewMode';
import { useWorkflowPreviewMode } from '../../hooks/useWorkflowPreviewMode';
import { WorkflowDescriptorOutline } from './outline/WorkflowDescriptorOutline';
import { WorkflowGraphViewport } from './graph/WorkflowGraphViewport';

interface WorkflowPreviewProps {
  descriptor: WorkflowDescriptor | null;
  activeStep?: {
    stepName?: string | null;
    stageName?: string | null;
    parallelGroup?: string | null;
    branchIndex?: number | null;
  } | null;
  className?: string;
}

export function WorkflowPreview({ descriptor, activeStep, className }: WorkflowPreviewProps) {
  const { mode, setMode } = useWorkflowPreviewMode('graph');

  return (
    <Tabs
      value={mode}
      onValueChange={(value) => setMode(value as WorkflowPreviewMode)}
      className={cn('flex h-full min-h-0 flex-col overflow-hidden', className)}
    >
      <div className="flex items-center justify-between gap-3 border-b border-white/10 bg-background/40 px-4 py-3 backdrop-blur-sm">
        <div className="min-w-0">
          <div className="text-xs uppercase tracking-wide text-foreground/50">Workflow preview</div>
          <div className="truncate text-sm font-semibold text-foreground">
            {descriptor?.display_name ?? 'Select a workflow'}
          </div>
        </div>

        <TabsList className="h-8">
          <TabsTrigger value="graph" className="h-7 gap-2 text-xs">
            <LayoutGrid className="h-3.5 w-3.5" />
            Graph
          </TabsTrigger>
          <TabsTrigger value="outline" className="h-7 gap-2 text-xs">
            <List className="h-3.5 w-3.5" />
            Outline
          </TabsTrigger>
        </TabsList>
      </div>

      <TabsContent
        value="graph"
        className="m-0 mt-0 flex-1 min-h-0 overflow-hidden data-[state=active]:block"
      >
        <WorkflowGraphViewport descriptor={descriptor} activeStep={activeStep} className="h-full" />
      </TabsContent>

      <TabsContent
        value="outline"
        className="m-0 mt-0 flex-1 min-h-0 overflow-hidden data-[state=active]:block"
      >
        <ScrollArea className="h-full min-h-0">
          <WorkflowDescriptorOutline descriptor={descriptor} />
        </ScrollArea>
      </TabsContent>
    </Tabs>
  );
}
