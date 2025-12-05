import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { GlassPanel } from '@/components/ui/foundation';
import type { WorkflowSummary } from '@/lib/api/client/types.gen';
import type { WorkflowRunListItemView } from '@/lib/workflows/types';
import { WorkflowRunsList } from './WorkflowRunsList';
import type { WorkflowStatusFilter } from '../constants';

interface Props {
  runs: WorkflowRunListItemView[];
  workflows: WorkflowSummary[];
  statusFilter: WorkflowStatusFilter;
  onStatusChange: (value: WorkflowStatusFilter) => void;
  onRefresh: () => void;
  onLoadMore?: () => void;
  hasMore: boolean;
  isLoading: boolean;
  isFetchingMore: boolean;
  onSelectRun: (runId: string, workflowKey?: string | null) => void;
  selectedRunId: string | null;
  onDeleteRun: (runId: string, conversationId?: string | null) => void;
  deletingRunId: string | null;
}

export function RunHistoryPanel({
  runs,
  workflows,
  statusFilter,
  onStatusChange,
  onRefresh,
  onLoadMore,
  hasMore,
  isLoading,
  isFetchingMore,
  onSelectRun,
  selectedRunId,
  onDeleteRun,
  deletingRunId,
}: Props) {
  return (
    <GlassPanel className="space-y-4 p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-sm font-semibold">Run history</div>
          <p className="text-xs text-foreground/60">Recent runs for the selected workflow.</p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={statusFilter} onValueChange={(value) => onStatusChange(value as WorkflowStatusFilter)}>
            <SelectTrigger className="w-36">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              <SelectItem value="running">Running</SelectItem>
              <SelectItem value="succeeded">Succeeded</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
              <SelectItem value="cancelled">Cancelled</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="ghost" size="sm" onClick={onRefresh}>
            Refresh
          </Button>
        </div>
      </div>

      <WorkflowRunsList
        runs={runs}
        workflows={workflows}
        isLoading={isLoading}
        isFetchingMore={isFetchingMore}
        hasMore={hasMore}
        onLoadMore={onLoadMore}
        onSelectRun={onSelectRun}
        selectedRunId={selectedRunId}
        onRefresh={onRefresh}
        onDeleteRun={onDeleteRun}
        deletingRunId={deletingRunId}
      />
    </GlassPanel>
  );
}
