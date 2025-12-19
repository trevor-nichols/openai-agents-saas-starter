'use client';

import { Badge } from '@/components/ui/badge';
import { InlineTag } from '@/components/ui/foundation';
import { EmptyState } from '@/components/ui/states';
import { cn } from '@/lib/utils';
import type { WorkflowDescriptor } from '@/lib/workflows/types';

import { WorkflowDescriptorCard } from './WorkflowDescriptorCard';

interface WorkflowDescriptorOutlineProps {
  descriptor: WorkflowDescriptor | null;
  className?: string;
}

export function WorkflowDescriptorOutline({ descriptor, className }: WorkflowDescriptorOutlineProps) {
  if (!descriptor) {
    return <EmptyState title="Select a workflow" description="Choose a workflow to preview its structure." />;
  }

  return (
    <div className={cn('mx-auto w-full max-w-4xl space-y-6 p-6', className)}>
      <WorkflowDescriptorCard descriptor={descriptor} />

      <div className="space-y-4">
        {descriptor.stages.map((stage, stageIndex) => (
          <section
            key={`${stage.name}-${stageIndex}`}
            className="rounded-xl border border-white/5 bg-white/5 p-4"
          >
            <header className="flex flex-wrap items-center justify-between gap-2">
              <div className="min-w-0">
                <h4 className="truncate text-sm font-semibold text-foreground">
                  {stageIndex + 1}. {stage.name}
                </h4>
                <p className="text-xs text-foreground/60">
                  {stage.mode === 'parallel'
                    ? 'Parallel stage (fan-out/fan-in).'
                    : 'Sequential stage (one step after another).'}
                </p>
              </div>
              <Badge variant="outline" className="capitalize">
                {stage.mode}
              </Badge>
            </header>

            <ol className="mt-4 space-y-2">
              {stage.steps.map((step, stepIndex) => (
                <li
                  key={`${stage.name}-${step.name}-${stepIndex}`}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-white/5 bg-background/40 px-3 py-2"
                >
                  <div className="min-w-0">
                    <div className="truncate text-sm font-medium text-foreground/90">
                      {stageIndex + 1}.{stepIndex + 1} {step.name}
                    </div>
                  </div>
                  <InlineTag tone="default">{step.agent_key}</InlineTag>
                </li>
              ))}
            </ol>
          </section>
        ))}
      </div>
    </div>
  );
}
