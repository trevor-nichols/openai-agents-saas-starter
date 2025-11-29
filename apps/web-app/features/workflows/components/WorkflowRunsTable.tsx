import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { SkeletonPanel, EmptyState } from '@/components/ui/states';
import { cn } from '@/lib/utils';
import type { WorkflowRunListItemView } from '@/lib/workflows/types';

interface WorkflowRunsTableProps {
  runs: WorkflowRunListItemView[];
  isLoading?: boolean;
  isFetchingMore?: boolean;
  hasMore?: boolean;
  onLoadMore?: () => void;
  onSelectRun: (runId: string, workflowKey: string) => void;
  selectedRunId?: string | null;
  onRefresh?: () => void;
}

const STATUS_VARIANT: Record<string, 'default' | 'secondary' | 'outline' | 'destructive'> = {
  running: 'default',
  succeeded: 'secondary',
  failed: 'destructive',
  cancelled: 'outline',
};

function formatDurationMs(ms?: number | null) {
  if (!ms && ms !== 0) return '—';
  const seconds = Math.floor(ms / 1000);
  const mins = Math.floor(seconds / 60);
  if (mins === 0) return `${seconds}s`;
  return `${mins}m ${seconds % 60}s`;
}

export function WorkflowRunsTable({
  runs,
  isLoading,
  isFetchingMore,
  hasMore,
  onLoadMore,
  onSelectRun,
  selectedRunId,
  onRefresh,
}: WorkflowRunsTableProps) {
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
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Run</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Started</TableHead>
            <TableHead>Duration</TableHead>
            <TableHead>Conversation</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {runs.map((run) => {
            const variant = STATUS_VARIANT[run.status] ?? 'outline';
            return (
              <TableRow
                key={run.workflow_run_id}
                className={cn('cursor-pointer', selectedRunId === run.workflow_run_id && 'bg-white/5')}
                onClick={() => onSelectRun(run.workflow_run_id, run.workflow_key)}
              >
                <TableCell className="font-mono text-xs">{run.workflow_run_id}</TableCell>
                <TableCell>
                  <Badge variant={variant} className="capitalize">
                    {run.status}
                  </Badge>
                </TableCell>
                <TableCell className="text-sm text-foreground/70">
                  {new Date(run.started_at).toLocaleString()}
                </TableCell>
                <TableCell className="text-sm text-foreground/70">
                  {formatDurationMs(run.duration_ms)}
                </TableCell>
                <TableCell className="text-sm text-foreground/70">
                  {run.conversation_id ?? '—'}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
        <TableCaption className="text-left text-xs text-foreground/60">
          {runs.length} run{runs.length === 1 ? '' : 's'} shown
        </TableCaption>
      </Table>

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
