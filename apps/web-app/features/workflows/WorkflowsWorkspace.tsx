'use client';

import { useMemo, useState } from 'react';

import { ErrorState } from '@/components/ui/states';
import { USE_API_MOCK } from '@/lib/config';
import {
  useWorkflowDescriptorQuery,
  useWorkflowRunEventsQuery,
  useWorkflowRunQuery,
  useWorkflowsQuery,
} from '@/lib/queries/workflows';
import type { LocationHint } from '@/lib/api/client/types.gen';
import { RunHistoryPanel } from './components/RunHistoryPanel';
import { RunConsole } from './components/RunConsole';
import { WorkflowSidebar } from './components/WorkflowSidebar';
import type { WorkflowStatusFilter } from './constants';
import {
  useWorkflowRunActions,
  useWorkflowRunStream,
  useWorkflowRunsInfinite,
  useWorkflowSelection,
} from './hooks';

export function WorkflowsWorkspace() {
  const { data: workflows = [], isLoading: isWorkflowsLoading, isError } = useWorkflowsQuery();
  const workflowKeys = useMemo(() => workflows.map((w) => w.key), [workflows]);

  const { selectedWorkflowKey, selectedRunId, setWorkflow, setRun, resetRun } = useWorkflowSelection(workflowKeys);

  const [statusFilter, setStatusFilter] = useState<WorkflowStatusFilter>('all');

  const descriptorQuery = useWorkflowDescriptorQuery(selectedWorkflowKey ?? null);

  const runFilters = useMemo(
    () => ({
      workflowKey: selectedWorkflowKey,
      runStatus: statusFilter === 'all' ? null : statusFilter,
      limit: 20,
    }),
    [selectedWorkflowKey, statusFilter],
  );

  const runs = useWorkflowRunsInfinite(runFilters);

  const runDetailQuery = useWorkflowRunQuery(selectedRunId ?? '', Boolean(selectedRunId));
  const runEventsQuery = useWorkflowRunEventsQuery(
    selectedRunId ?? null,
    runDetailQuery.data?.conversation_id ?? null,
  );

  const {
    events: streamEvents,
    status: streamStatus,
    error: runError,
    isStreaming,
    lastSummary,
    lastUpdated,
    startRun,
    simulate,
  } = useWorkflowRunStream({
    onRunCreated: (runId, workflowKey) => setRun(runId, workflowKey ?? selectedWorkflowKey),
  });

  const { cancelRun, deleteRun, deletingRunId, cancelPending } = useWorkflowRunActions({
    selectedRunId,
    onRunDeselected: () => {
      resetRun();
    },
    onAfterDelete: async () => {
      await runs.refetch();
      await runDetailQuery.refetch();
      await runEventsQuery.refetch();
    },
  });

  const handleRun = async (input: {
    workflowKey: string;
    message: string;
    shareLocation?: boolean;
    location?: LocationHint | null;
  }) => {
    await startRun(input);
    await runs.refetch();
  };

  if (isError) {
    return <ErrorState title="Unable to load workflows" />;
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[320px_minmax(0,1fr)_320px]">
      <WorkflowSidebar
        workflows={workflows}
        isLoadingWorkflows={isWorkflowsLoading}
        selectedKey={selectedWorkflowKey}
        onSelect={setWorkflow}
        descriptor={descriptorQuery.data ?? null}
        isLoadingDescriptor={descriptorQuery.isLoading}
      />

      <div className="space-y-4">
        <RunConsole
          workflows={workflows}
          selectedWorkflowKey={selectedWorkflowKey}
          onRun={handleRun}
          isRunning={isStreaming}
          isLoadingWorkflows={isWorkflowsLoading}
          runError={runError}
          streamStatus={streamStatus}
          isMockMode={USE_API_MOCK}
          onSimulate={simulate}
          streamEvents={streamEvents}
          lastRunSummary={lastSummary}
          lastUpdated={lastUpdated}
          selectedRunId={selectedRunId}
          runDetail={runDetailQuery.data ?? null}
          runEvents={runEventsQuery.data ?? null}
          isLoadingRun={runDetailQuery.isLoading}
          isLoadingEvents={runEventsQuery.isLoading}
          onCancelRun={cancelRun}
          cancelPending={cancelPending}
          onDeleteRun={deleteRun}
          deletingRunId={deletingRunId}
        />
      </div>

      <RunHistoryPanel
        runs={runs.runs}
        workflows={workflows}
        statusFilter={statusFilter}
        onStatusChange={setStatusFilter}
        onRefresh={runs.refetch}
        onLoadMore={runs.loadMore}
        hasMore={runs.hasMore}
        isLoading={runs.isInitialLoading}
        isFetchingMore={runs.isLoadingMore}
        onSelectRun={(runId, workflowKey) => setRun(runId, workflowKey ?? selectedWorkflowKey)}
        selectedRunId={selectedRunId}
        onDeleteRun={deleteRun}
        deletingRunId={deletingRunId}
      />
    </div>
  );
}
