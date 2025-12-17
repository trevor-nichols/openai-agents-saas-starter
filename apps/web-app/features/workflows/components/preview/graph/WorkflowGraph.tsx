"use client";

import { createRef, useMemo, useRef, type RefObject } from 'react';

import { AnimatedBeam } from '@/components/ui/beam';
import { cn } from '@/lib/utils';
import type { WorkflowDescriptor, WorkflowStageDescriptor } from '@/lib/workflows/types';

type ActiveStep = {
  stepName?: string | null;
  stageName?: string | null;
  parallelGroup?: string | null;
  branchIndex?: number | null;
};

type Props = {
  descriptor: WorkflowDescriptor | null;
  className?: string;
  activeStep?: ActiveStep | null;
};

type StepRef = {
  key: string;
  stageIndex: number;
  stepIndex: number;
  stage: WorkflowStageDescriptor;
  label: string;
  ref: RefObject<HTMLDivElement | null>;
};

type Edge = {
  fromKey: string;
  toKey: string;
  curvature?: number;
  pathColor?: string;
  gradientStartColor?: string;
  gradientStopColor?: string;
  reverse?: boolean;
};

function keyFor(stageIndex: number, stepIndex: number) {
  return `${stageIndex}-${stepIndex}`;
}

export function WorkflowGraph({ descriptor, className, activeStep }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);

  const stepRefs: StepRef[] = useMemo(() => {
    if (!descriptor?.stages?.length) return [];
    return descriptor.stages.flatMap((stage, stageIndex) =>
      stage.steps.map((step, stepIndex) => ({
        key: keyFor(stageIndex, stepIndex),
        stageIndex,
        stepIndex,
        stage,
        label: step.name,
        ref: createRef<HTMLDivElement>(),
      })),
    );
  }, [descriptor]);

  const refMap = useMemo(() => {
    const map = new Map<string, RefObject<HTMLDivElement | null>>();
    stepRefs.forEach((item) => map.set(item.key, item.ref));
    return map;
  }, [stepRefs]);

  const edges: Edge[] = useMemo(() => {
    if (!descriptor?.stages?.length) return [];
    const built: Edge[] = [];

    descriptor.stages.forEach((stage, stageIndex) => {
      const stepCount = stage.steps.length;
      // Sequential edges within the stage
      if (stage.mode === 'sequential' && stepCount > 1) {
        for (let i = 0; i < stepCount - 1; i += 1) {
          built.push({
            fromKey: keyFor(stageIndex, i),
            toKey: keyFor(stageIndex, i + 1),
            curvature: 0,
            pathColor: '#64748b',
            gradientStartColor: '#6366f1',
            gradientStopColor: '#22c55e',
          });
        }
      }

      // Edges to the next stage (fan-out / fan-in)
      const nextStage = descriptor.stages[stageIndex + 1];
      if (!nextStage) return;

      const fromKeys = stage.mode === 'parallel'
        ? stage.steps.map((_, idx) => keyFor(stageIndex, idx))
        : [keyFor(stageIndex, stepCount - 1)];

      const toKeys = nextStage.mode === 'parallel'
        ? nextStage.steps.map((_, idx) => keyFor(stageIndex + 1, idx))
        : [keyFor(stageIndex + 1, 0)];

      fromKeys.forEach((fromKey, fromIdx) => {
        toKeys.forEach((toKey, toIdx) => {
          built.push({
            fromKey,
            toKey,
            curvature: 40 + 10 * (fromIdx + toIdx),
            pathColor: '#a855f7',
            gradientStartColor: '#6366f1',
            gradientStopColor: '#a855f7',
            reverse: false,
          });
        });
      });
    });

    return built;
  }, [descriptor]);

  const activeKey = useMemo(() => {
    if (!activeStep || !stepRefs.length) return null;
    const candidate = stepRefs.find((step) => {
      const nameMatch = activeStep.stepName ? step.label === activeStep.stepName : false;
      const stageMatch = activeStep.stageName ? step.stage.name === activeStep.stageName : false;
      const branchMatch = activeStep.branchIndex == null || activeStep.branchIndex === step.stepIndex;

      if (activeStep.stepName) {
        return nameMatch && branchMatch;
      }
      if (activeStep.stageName) {
        return stageMatch && branchMatch;
      }
      if (activeStep.parallelGroup) {
        const parallelMatch = step.stage.name === activeStep.parallelGroup;
        return parallelMatch && branchMatch;
      }
      return false;
    });
    return candidate?.key ?? null;
  }, [activeStep, stepRefs]);

  if (!descriptor) {
    return (
      <div className={cn('rounded-lg border border-white/5 bg-white/5 p-4', className)}>
        <p className="text-sm text-foreground/70">Select a workflow to preview its structure.</p>
      </div>
    );
  }

  const palette = ['#7c3aed', '#0ea5e9', '#22c55e', '#f59e0b', '#ec4899'];

  return (
    <div className={cn('relative overflow-hidden rounded-lg border border-white/5 bg-white/5 p-4', className)}>
      <div className="mb-3 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-wide text-foreground/50">Workflow graph</p>
          <p className="text-sm font-semibold text-foreground">{descriptor.display_name}</p>
        </div>
        <div className="flex items-center gap-2 text-[11px] text-foreground/60">
          <span className="inline-flex h-2 w-2 rounded-full bg-primary/80" /> Sequential
          <span className="inline-flex h-2 w-2 rounded-full bg-purple-400" /> Parallel
        </div>
      </div>

      <div ref={containerRef} className="relative grid min-h-[240px] grid-cols-1 gap-6 md:grid-cols-[repeat(auto-fit,minmax(160px,1fr))]">
        {/* Beams */}
        {edges.map((edge, idx) => {
          const fromRef = refMap.get(edge.fromKey);
          const toRef = refMap.get(edge.toKey);
          if (!fromRef || !toRef) return null;
          const isActiveEdge = activeKey ? edge.toKey === activeKey : false;
          return (
            <AnimatedBeam
              key={`${edge.fromKey}-${edge.toKey}-${idx}`}
              containerRef={containerRef}
              fromRef={fromRef}
              toRef={toRef}
              curvature={edge.curvature}
              pathColor={edge.pathColor}
              gradientStartColor={edge.gradientStartColor}
              gradientStopColor={edge.gradientStopColor}
              pathOpacity={isActiveEdge ? 0.4 : 0.15}
              pathWidth={isActiveEdge ? 3 : 2}
              duration={isActiveEdge ? 4 : 12}
              animated={isActiveEdge}
            />
          );
        })}

        {/* Nodes */}
        {descriptor.stages.map((stage, stageIndex) => {
          const stageColor = palette[stageIndex % palette.length];
          return (
            <div key={stage.name} className="relative flex flex-col gap-3 rounded-lg border border-white/5 bg-white/5 p-3">
              <div className="flex items-center justify-between text-xs text-foreground/70">
                <span className="font-semibold text-foreground">{stage.name}</span>
                <span className={cn('rounded-full px-2 py-0.5', stage.mode === 'parallel' ? 'bg-purple-500/15 text-purple-100' : 'bg-primary/10 text-primary')}>
                  {stage.mode}
                </span>
              </div>

              <div className="flex flex-col gap-2">
                {stage.steps.map((step, stepIndex) => {
                  const ref = refMap.get(keyFor(stageIndex, stepIndex));
                  const isActive = activeKey === keyFor(stageIndex, stepIndex);
                  return (
                    <div
                      key={step.name + stepIndex}
                      ref={ref}
                      className={cn(
                        'relative flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-3 py-2 shadow-sm backdrop-blur transition-colors',
                        stage.mode === 'parallel' ? 'ring-1 ring-purple-500/30' : 'ring-1 ring-primary/20',
                        isActive ? 'bg-white/20 ring-2 ring-emerald-400/60' : null,
                      )}
                    >
                      <span className="inline-flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full text-[11px] font-semibold" style={{ backgroundColor: `${stageColor}33`, color: stageColor }}>
                        {stageIndex + 1}.{stepIndex + 1}
                      </span>
                      <div className="min-w-0 text-sm font-medium text-foreground/90 truncate" title={step.name}>
                        {step.name}
                      </div>
                      <div className="ml-auto text-[11px] uppercase tracking-wide text-foreground/40">{step.agent_key}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
