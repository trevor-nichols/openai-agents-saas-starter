'use client';

import { useMemo, useState } from 'react';

import { ErrorState } from '@/components/ui/states';
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '@/components/ui/resizable';
import { USE_API_MOCK } from '@/lib/config';
import {
  useWorkflowDescriptorQuery,
  useWorkflowRunQuery,
  useWorkflowRunReplayEventsQuery,
  useWorkflowsQuery,
} from '@/lib/queries/workflows';
import type { LocationHint } from '@/lib/api/client/types.gen';

import { WorkflowCanvas, WorkflowRunFeed, WorkflowSidebar } from './components';
import type { WorkflowStatusFilter } from './constants';
import {
  useWorkflowRunActions,
  useWorkflowRunStream,
  useWorkflowNodeStreamStore,
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

  const activeStreamStep = useMemo(() => {
    // Pick the latest event that carries step metadata
    for (let i = streamEvents.length - 1; i >= 0; i -= 1) {
      const evt = streamEvents[i];
      if (!evt) continue;
      const workflow = evt.workflow;
      if (workflow?.step_name || workflow?.stage_name || workflow?.parallel_group) {
        return {
          stepName: workflow?.step_name ?? null,
          stageName: workflow?.stage_name ?? null,
          parallelGroup: workflow?.parallel_group ?? null,
          branchIndex: typeof workflow?.branch_index === 'number' ? workflow.branch_index : null,
        } as const;
      }
    }
    return null;
  }, [streamEvents]);

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
