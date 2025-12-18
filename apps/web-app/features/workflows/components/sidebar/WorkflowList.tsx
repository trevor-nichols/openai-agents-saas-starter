import { SkeletonPanel } from '@/components/ui/states';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { InlineTag } from '@/components/ui/foundation';
import { cn } from '@/lib/utils';
import type { WorkflowSummaryView } from '@/lib/workflows/types';

interface WorkflowListProps {
  items: WorkflowSummaryView[];
  isLoading?: boolean;
  selectedKey?: string | null;
  onSelect: (workflowKey: string) => void;
}

export function WorkflowList({ items, isLoading, selectedKey, onSelect }: WorkflowListProps) {
  if (isLoading) {
    return <SkeletonPanel lines={6} />;
  }

  if (!items.length) {
    return (
      <div className="rounded-lg border border-white/5 bg-white/5 p-4 text-sm text-foreground/70">
        No workflows available.
      </div>
    );
  }

  return (
    <RadioGroup
      value={selectedKey ?? undefined}
      onValueChange={(value) => onSelect(value)}
      className="flex flex-col gap-2"
    >
      {items.map((workflow) => {
        const active = workflow.key === selectedKey;
        return (
          <label
            key={workflow.key}
            htmlFor={`workflow-${workflow.key}`}
            className={cn(
              'flex min-w-0 cursor-pointer items-start gap-3 rounded-lg border px-3 py-3 transition',
              'hover:border-primary/30 hover:bg-primary/5 focus-within:ring-2 focus-within:ring-primary/40',
              active
                ? 'border-primary/60 bg-primary/10 shadow-sm'
                : 'border-white/5 bg-white/5'
            )}
          >
            <RadioGroupItem id={`workflow-${workflow.key}`} value={workflow.key} className="mt-1 shrink-0" />
            <div className="min-w-0 flex-1 space-y-1">
              <div className="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1">
                <div className="min-w-0 flex-1 truncate text-sm font-semibold">
                  {workflow.display_name}
                </div>
                {workflow.default ? (
                  <InlineTag
                    className="max-w-full shrink-0 px-2 py-0.5 text-[10px] uppercase tracking-wide"
                    tone="default"
                  >
                    Default
                  </InlineTag>
                ) : null}
              </div>
              {workflow.description ? (
                <p className="line-clamp-2 text-xs text-foreground/70">{workflow.description}</p>
              ) : null}
              <p className="text-[11px] text-foreground/50">Steps: {workflow.step_count}</p>
            </div>
          </label>
        );
      })}
    </RadioGroup>
  );
}
