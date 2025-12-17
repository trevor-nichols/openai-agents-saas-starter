import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { InlineTag } from '@/components/ui/foundation';
import { SkeletonPanel, EmptyState } from '@/components/ui/states';
import { cn } from '@/lib/utils';
import type { WorkflowRunListItemView } from '@/lib/workflows/types';
import type { WorkflowSummary } from '@/lib/api/client/types.gen';
import { workflowRunStatusVariant } from '../../../constants';
import { WorkflowRunDeleteButton } from '../actions/WorkflowRunDeleteButton';

interface WorkflowRunsListProps {
  runs: WorkflowRunListItemView[];
  workflows?: WorkflowSummary[];
  isLoading?: boolean;
  isFetchingMore?: boolean;
  hasMore?: boolean;
  onLoadMore?: () => void;
  onSelectRun: (runId: string, workflowKey: string) => void;
  selectedRunId?: string | null;
  onRefresh?: () => void;
  onDeleteRun?: (runId: string, conversationId?: string | null) => void | Promise<void>;
  deletingRunId?: string | null;
}

function formatTimestamp(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  return `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
}

function summarize(run: WorkflowRunListItemView): string {
  if (run.final_output_text) return run.final_output_text.slice(0, 120);
  return `Run ${run.workflow_run_id}`;
}

export function WorkflowRunsList({
  runs,
  workflows,
  isLoading,
  isFetchingMore,
  hasMore,
  onLoadMore,
  onSelectRun,
  selectedRunId,
  onRefresh,
  onDeleteRun,
  deletingRunId,
}: WorkflowRunsListProps) {
  if (isLoading) {
    return <SkeletonPanel lines={6} />;
  }

  if (!runs.length) {
    return (
      <EmptyState
        title="No runs yet"
        description="Run a workflow to see history here."
        action={
          onRefresh ? (
            <Button size="sm" variant="outline" onClick={onRefresh}>
              Refresh
            </Button>
          ) : undefined
        }
      />
    );
  }

  return (
    <div className="space-y-2">
      {runs.map((run) => {
        const active = run.workflow_run_id === selectedRunId;
        const variant = workflowRunStatusVariant(run.status);
        const workflowLabel = workflows?.find((w) => w.key === run.workflow_key)?.display_name ?? run.workflow_key;
        return (
          <div
            key={run.workflow_run_id}
            role="button"
            tabIndex={0}
            className={cn(
              'w-full rounded-lg border px-4 py-3 text-left transition focus:outline-none focus:ring-2 focus:ring-primary/60',
              active ? 'border-primary/60 bg-primary/10' : 'border-white/5 bg-white/5 hover:border-white/10'
            )}
            onClick={() => onSelectRun(run.workflow_run_id, run.workflow_key)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onSelectRun(run.workflow_run_id, run.workflow_key);
              }
            }}
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <Badge variant={variant} className="capitalize">
                  {run.status}
                </Badge>
                <InlineTag tone="default">{workflowLabel}</InlineTag>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-foreground/60">{formatTimestamp(run.started_at)}</span>
                {onDeleteRun ? (
                  <WorkflowRunDeleteButton
                    onConfirm={() => onDeleteRun(run.workflow_run_id, run.conversation_id ?? null)}
                    pending={deletingRunId === run.workflow_run_id}
                    tooltip="Delete run"
                    stopPropagation
                  />
                ) : null}
              </div>
            </div>
            <p className="mt-2 text-sm text-foreground font-semibold line-clamp-1">{summarize(run)}</p>
          </div>
        );
      })}

      {hasMore && onLoadMore ? (
        <div className="flex justify-end">
          <Button size="sm" variant="outline" onClick={onLoadMore} disabled={isFetchingMore}>
            {isFetchingMore ? 'Loading…' : 'Load more'}
          </Button>
        </div>
      ) : null}
    </div>
  );
}
