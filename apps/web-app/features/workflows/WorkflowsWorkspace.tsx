'use client';

import { useMemo, useState } from 'react';

import { ErrorState } from '@/components/ui/states';
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '@/components/ui/resizable';
import { USE_API_MOCK } from '@/lib/config';
import { useContainersQuery } from '@/lib/queries/containers';
import { useVectorStoresQuery } from '@/lib/queries/vectorStores';
import { useTools } from '@/lib/queries/tools';
import {
  useWorkflowDescriptorQuery,
  useWorkflowRunQuery,
  useWorkflowRunReplayEventsQuery,
  useWorkflowsQuery,
} from '@/lib/queries/workflows';

import { WorkflowCanvas, WorkflowRunFeed, WorkflowSidebar } from './components';
import type { WorkflowStatusFilter } from './constants';
import {
  useActiveStreamStep,
  useWorkflowCapabilities,
  useWorkflowOverrides,
  useWorkflowRunLauncher,
  useWorkflowRunActions,
  useWorkflowRunStream,
  useWorkflowNodeStreamStore,
  useWorkflowRunsInfinite,
  useWorkflowSelection,
} from './hooks';

function getQueryErrorMessage(error: unknown): string | null {
  if (!error) return null;
  if (error instanceof Error) {
    return error.message;
  }
  return String(error);
}

export function WorkflowsWorkspace() {
  const { data: workflows = [], isLoading: isWorkflowsLoading, isError } = useWorkflowsQuery();
  const workflowKeys = useMemo(() => workflows.map((w) => w.key), [workflows]);

  const { selectedWorkflowKey, selectedRunId, setWorkflow, setRun, resetRun } = useWorkflowSelection(workflowKeys);

  const [statusFilter, setStatusFilter] = useState<WorkflowStatusFilter>('all');

  const descriptorQuery = useWorkflowDescriptorQuery(selectedWorkflowKey ?? null);
  const toolsQuery = useTools();
  const containersQuery = useContainersQuery();
  const vectorStoresQuery = useVectorStoresQuery();
  const { containerOverrides, vectorStoreOverrides, setContainerOverride, setVectorStoreOverride } =
    useWorkflowOverrides(selectedWorkflowKey);

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
  const runReplayQuery = useWorkflowRunReplayEventsQuery(selectedRunId ?? null);

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

  const nodeStreamStore = useWorkflowNodeStreamStore({
    descriptor: descriptorQuery.data ?? null,
    events: streamEvents,
  });

  const { toolsByAgent, supportsContainersByAgent, supportsFileSearchByAgent } = useWorkflowCapabilities(
    descriptorQuery.data ?? null,
    toolsQuery.tools,
  );

  const containersError = getQueryErrorMessage(containersQuery.error);
  const vectorStoresError = getQueryErrorMessage(vectorStoresQuery.error);

  const activeStreamStep = useActiveStreamStep(streamEvents);

  const { cancelRun, deleteRun, deletingRunId, cancelPending } = useWorkflowRunActions({
    selectedRunId,
    onRunDeselected: () => {
      resetRun();
    },
    onAfterDelete: async () => {
      await runs.refetch();
      await runDetailQuery.refetch();
      await runReplayQuery.refetch();
    },
  });

  const handleRun = useWorkflowRunLauncher({
    startRun,
    containerOverrides,
    vectorStoreOverrides,
    supportsContainersByAgent,
    supportsFileSearchByAgent,
    onAfterRun: async () => {
      await runs.refetch();
    },
  });

  if (isError) {
    return <ErrorState title="Unable to load workflows" />;
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
      <ResizablePanelGroup direction="horizontal" className="h-full min-h-0 border-t">
        <ResizablePanel defaultSize={20} minSize={15} maxSize={30} className="min-h-0 bg-background">
          <WorkflowSidebar
            workflows={workflows}
            isLoadingWorkflows={isWorkflowsLoading}
            selectedKey={selectedWorkflowKey}
            onSelect={setWorkflow}
          />
        </ResizablePanel>

        <ResizableHandle />

        <ResizablePanel defaultSize={55} minSize={30} className="min-h-0 bg-muted/5 relative">
          <WorkflowCanvas
            descriptor={descriptorQuery.data ?? null}
            nodeStreamStore={nodeStreamStore}
            activeStep={activeStreamStep}
            toolsByAgent={toolsByAgent}
            supportsContainersByAgent={supportsContainersByAgent}
            supportsFileSearchByAgent={supportsFileSearchByAgent}
            containers={containersQuery.data?.items ?? []}
            containersError={containersError}
            isLoadingContainers={containersQuery.isLoading}
            containerOverrides={containerOverrides}
            onContainerOverrideChange={setContainerOverride}
            vectorStores={vectorStoresQuery.data?.items ?? []}
            vectorStoresError={vectorStoresError}
            isLoadingVectorStores={vectorStoresQuery.isLoading}
            vectorStoreOverrides={vectorStoreOverrides}
            onVectorStoreOverrideChange={setVectorStoreOverride}
            selectedKey={selectedWorkflowKey}
            onRun={handleRun}
            isRunning={isStreaming}
            runError={runError}
            isLoadingWorkflows={isWorkflowsLoading}
            streamStatus={streamStatus}
          />
        </ResizablePanel>

        <ResizableHandle />

        <ResizablePanel defaultSize={25} minSize={20} maxSize={40} className="min-h-0 bg-background">
          <WorkflowRunFeed
            workflows={workflows}
            streamEvents={streamEvents}
            streamStatus={streamStatus}
            runError={runError}
            isMockMode={USE_API_MOCK}
            onSimulate={simulate}
            lastRunSummary={lastSummary}
            lastUpdated={lastUpdated}
            selectedRunId={selectedRunId}
            runDetail={runDetailQuery.data ?? null}
            runReplayEvents={runReplayQuery.data ?? null}
            isLoadingRun={runDetailQuery.isLoading}
            isLoadingReplay={runReplayQuery.isLoading}
            onCancelRun={cancelRun}
            cancelPending={cancelPending}
            onDeleteRun={deleteRun}
            deletingRunId={deletingRunId}
            historyRuns={runs.runs}
            historyStatusFilter={statusFilter}
            onHistoryStatusChange={setStatusFilter}
            onHistoryRefresh={runs.refetch}
            onHistoryLoadMore={runs.loadMore}
            historyHasMore={runs.hasMore}
            isHistoryLoading={runs.isInitialLoading}
            isHistoryFetchingMore={runs.isLoadingMore}
            onSelectRun={(runId, workflowKey) => setRun(runId, workflowKey ?? selectedWorkflowKey)}
          />
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}
