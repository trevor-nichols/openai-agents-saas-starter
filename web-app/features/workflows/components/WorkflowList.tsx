import { SkeletonPanel } from '@/components/ui/states';
import { Button } from '@/components/ui/button';
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
    <div className="space-y-2">
      {items.map((workflow) => {
        const active = workflow.key === selectedKey;
        return (
          <Button
            key={workflow.key}
            onClick={() => onSelect(workflow.key)}
            variant={active ? 'default' : 'ghost'}
            className={cn(
              'w-full justify-start rounded-lg border px-4 py-3 text-left transition',
              active
                ? 'border-primary/60 bg-primary/10 text-primary-foreground'
                : 'border-white/5 bg-white/5 hover:border-white/10'
            )}
          >
            <div className="flex items-center justify-between gap-2">
              <div className="text-sm font-semibold">{workflow.display_name}</div>
              {workflow.default ? (
                <span className="text-[11px] uppercase tracking-wide text-primary">Default</span>
              ) : null}
            </div>
            {workflow.description ? (
              <p className="mt-1 text-xs text-foreground/70">{workflow.description}</p>
            ) : null}
              <p className="mt-1 text-[11px] text-foreground/50">Steps: {workflow.step_count}</p>
          </Button>
        );
      })}
    </div>
  );
}
