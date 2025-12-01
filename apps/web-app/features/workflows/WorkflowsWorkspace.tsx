'use client';

import { useCallback, useEffect, useMemo, useState, useRef } from 'react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';

import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { InlineTag } from '@/components/ui/foundation';
import { GlassPanel, SectionHeader } from '@/components/ui/foundation';
import { ErrorState, SkeletonPanel } from '@/components/ui/states';
import {
  useCancelWorkflowRunMutation,
  useWorkflowDescriptorQuery,
  useWorkflowRunEventsQuery,
  useWorkflowRunQuery,
  useWorkflowRunsQuery,
  useWorkflowsQuery,
} from '@/lib/queries/workflows';
import type { StreamingWorkflowEvent, WorkflowRunRequestBody } from '@/lib/api/client/types.gen';
import { USE_API_MOCK } from '@/lib/config';
import { listWorkflowRuns } from '@/lib/api/workflows';
import { mockWorkflowStream } from '@/lib/workflows/mock';
import { streamWorkflowRun } from '@/lib/api/workflows';
import type { WorkflowRunListFilters, WorkflowRunListItemView } from '@/lib/workflows/types';
import { WorkflowList } from './components/WorkflowList';
import { WorkflowRunPanel } from './components/WorkflowRunPanel';
import { WorkflowStreamLog } from './components/WorkflowStreamLog';
import { WorkflowDescriptorCard } from './components/WorkflowDescriptorCard';
import { WorkflowRunsList } from './components/WorkflowRunsList';
import { WorkflowRunConversation } from './components/WorkflowRunConversation';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';

type StreamEventWithMeta = StreamingWorkflowEvent & { receivedAt: string };

type StreamStatus = 'idle' | 'connecting' | 'streaming' | 'completed' | 'error';

export function WorkflowsWorkspace() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const pathname = usePathname();

  const { data: workflows = [], isLoading, isError } = useWorkflowsQuery();
  const selectedKeyFromUrl = searchParams.get('workflow');
  const selectedRunId = searchParams.get('run');

  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<'all' | 'running' | 'succeeded' | 'failed' | 'cancelled'>('all');
  const [runs, setRuns] = useState<WorkflowRunListItemView[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const selectedRunIdRef = useRef<string | null>(selectedRunId);
  const workflowKeyRef = useRef<string | null>(null);
  const statusFilterRef = useRef<typeof statusFilter>(statusFilter);
  const nextCursorRef = useRef<string | null>(null);

  const [streamEvents, setStreamEvents] = useState<StreamEventWithMeta[]>([]);
  const [runError, setRunError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamStatus, setStreamStatus] = useState<StreamStatus>('idle');
  const [isTranscriptOpen, setIsTranscriptOpen] = useState(false);
  const [lastRunSummary, setLastRunSummary] = useState<{
    workflowKey: string;
    runId?: string | null;
    message?: string;
  } | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const updateUrl = useCallback(
    (updates: { workflow?: string | null; run?: string | null }) => {
      const params = new URLSearchParams(searchParams);
      if (updates.workflow !== undefined) {
        if (updates.workflow) params.set('workflow', updates.workflow);
        else params.delete('workflow');
      }
      if (updates.run !== undefined) {
        if (updates.run) params.set('run', updates.run);
        else params.delete('run');
      }
      router.replace(`${pathname}?${params.toString()}`, { scroll: false });
    },
    [pathname, router, searchParams],
  );

  useEffect(() => {
    setSelectedKey(selectedKeyFromUrl);
  }, [selectedKeyFromUrl]);

  useEffect(() => {
    selectedRunIdRef.current = selectedRunId;
    if (!selectedRunId) {
      setIsTranscriptOpen(false);
    }
  }, [selectedRunId]);

  const initialKey = useMemo(() => workflows[0]?.key ?? null, [workflows]);
  const effectiveSelectedKey = selectedKey ?? selectedKeyFromUrl ?? initialKey;

  useEffect(() => {
    workflowKeyRef.current = effectiveSelectedKey ?? null;
  }, [effectiveSelectedKey]);

  useEffect(() => {
    statusFilterRef.current = statusFilter;
  }, [statusFilter]);

  // ensure URL has a workflow once data arrives
  useEffect(() => {
    if (!selectedKeyFromUrl && workflows[0]?.key) {
      updateUrl({ workflow: workflows[0].key, run: null });
    }
  }, [selectedKeyFromUrl, workflows, updateUrl]);

  const descriptorQuery = useWorkflowDescriptorQuery(effectiveSelectedKey ?? null);

  const runFilters: WorkflowRunListFilters = useMemo(
    () => ({
      workflowKey: effectiveSelectedKey,
      runStatus: statusFilter === 'all' ? null : statusFilter,
      limit: 20,
    }),
    [effectiveSelectedKey, statusFilter],
  );

  const runsQuery = useWorkflowRunsQuery(runFilters);
  const runDetailQuery = useWorkflowRunQuery(selectedRunId ?? '', Boolean(selectedRunId));
  const runEventsQuery = useWorkflowRunEventsQuery(
    selectedRunId ?? null,
    runDetailQuery.data?.conversation_id ?? null,
  );
  const cancelRunMutation = useCancelWorkflowRunMutation();

  // reset runs when workflow or filter changes
  useEffect(() => {
    setNextCursor(null);
    setRuns([]);
  }, [effectiveSelectedKey, statusFilter]);

  // load first page
  useEffect(() => {
    if (!runsQuery.data) return;
    setNextCursor(runsQuery.data.next_cursor ?? null);
    nextCursorRef.current = runsQuery.data.next_cursor ?? null;
    setRuns(runsQuery.data.items);
  }, [runsQuery.data]);

  const handleSelectWorkflow = (workflowKey: string) => {
    setSelectedKey(workflowKey);
    updateUrl({ workflow: workflowKey, run: null });
  };

  const handleSelectRun = (runId: string, workflowKey?: string | null) => {
    const targetWorkflow = workflowKey ?? effectiveSelectedKey ?? null;
    updateUrl({ workflow: targetWorkflow, run: runId });
  };

  const handleRun = async (input: {
    workflowKey: string;
    message: string;
    shareLocation?: boolean;
  }) => {
    setRunError(null);
    setStreamEvents([]);
    setIsStreaming(true);
    setStreamStatus('connecting');
    setLastRunSummary({ workflowKey: input.workflowKey, runId: null, message: input.message });
    setLastUpdated(null);
    let autoSelected = selectedRunIdRef.current !== null;
    try {
      const body: WorkflowRunRequestBody = {
        message: input.message,
        share_location: input.shareLocation ?? null,
      };

      for await (const evt of streamWorkflowRun(input.workflowKey, body)) {
        const enriched: StreamEventWithMeta = { ...evt, receivedAt: new Date().toISOString() };
        setStreamEvents((prev): StreamEventWithMeta[] => [...prev, enriched]);
        setStreamStatus((current) => (current === 'connecting' ? 'streaming' : current));
        setLastUpdated(enriched.receivedAt);
        if (evt.kind === 'error') {
          const maybeMessage =
            typeof (evt as { payload?: { message?: string } }).payload?.message === 'string'
              ? (evt as { payload?: { message?: string } }).payload?.message
              : undefined;
          setRunError(maybeMessage ?? 'Workflow reported an error.');
        }
        setLastRunSummary((prev) => ({
          workflowKey: prev?.workflowKey ?? input.workflowKey,
          runId: prev?.runId ?? evt.workflow_run_id ?? null,
          message: prev?.message ?? input.message,
        }));
        if (!autoSelected && evt.workflow_run_id) {
          const runWorkflowKey = evt.workflow_key ?? input.workflowKey;
          handleSelectRun(evt.workflow_run_id, runWorkflowKey);
          selectedRunIdRef.current = evt.workflow_run_id;
          autoSelected = true;
        }
        if (evt.is_terminal) {
          setStreamStatus(evt.kind === 'error' ? 'error' : 'completed');
          break;
        }
      }
    } catch (error) {
      setRunError(error instanceof Error ? error.message : 'Failed to run workflow');
      setStreamStatus('error');
    } finally {
      setIsStreaming(false);
      await runsQuery.refetch();
    }
  };

  const handleSimulateStream = async () => {
    setRunError(null);
    setStreamEvents([]);
    const runId = `mock_run_${Date.now()}`;
    for await (const evt of mockWorkflowStream(runId)) {
      const enriched: StreamEventWithMeta = { ...evt, receivedAt: new Date().toISOString() };
      setStreamEvents((prev): StreamEventWithMeta[] => [...prev, enriched]);
    }
  };

  const handleCancelRun = () => {
    if (!selectedRunId) return;
    cancelRunMutation.mutate(selectedRunId);
  };

  const handleLoadMore = async () => {
    if (!nextCursor || !effectiveSelectedKey) return;
    const requestKey = workflowKeyRef.current;
    const requestStatus = statusFilterRef.current === 'all' ? null : statusFilterRef.current;
    const requestCursor = nextCursorRef.current;
    setIsLoadingMore(true);
    try {
      const page = await listWorkflowRuns({
        workflowKey: requestKey,
        runStatus: requestStatus,
        cursor: requestCursor,
        limit: 20,
      });
      const stillCurrent =
        requestKey === workflowKeyRef.current &&
        requestStatus === (statusFilterRef.current === 'all' ? null : statusFilterRef.current) &&
        requestCursor === nextCursorRef.current;
      if (!stillCurrent) {
        return;
      }
      setRuns((prev) => [...prev, ...page.items]);
      setNextCursor(page.next_cursor ?? null);
      nextCursorRef.current = page.next_cursor ?? null;
    } finally {
      setIsLoadingMore(false);
    }
  };

  const isRunsInitialLoading = runsQuery.isLoading && !runs.length;

  if (isError) {
    return <ErrorState title="Unable to load workflows" />;
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[320px_minmax(0,1fr)_320px]">
      <div className="space-y-3">
        <SectionHeader title="Workflows" description="Run multi-step workflows with streaming output." />
        <GlassPanel className="p-4 space-y-4">
          <WorkflowList
            items={workflows}
            isLoading={isLoading}
            selectedKey={effectiveSelectedKey}
            onSelect={handleSelectWorkflow}
          />
          <div className="border-t border-white/5 pt-3">
            <WorkflowDescriptorCard descriptor={descriptorQuery.data ?? null} isLoading={descriptorQuery.isLoading} />
          </div>
        </GlassPanel>
      </div>

      <div className="space-y-4">
        <GlassPanel className="p-4 space-y-4">
          {isLoading && !workflows.length ? (
            <SkeletonPanel lines={8} />
          ) : (
            <WorkflowRunPanel
              selectedKey={effectiveSelectedKey}
              onRun={handleRun}
              isRunning={isStreaming}
              runError={runError}
              isLoadingWorkflows={isLoading}
              streamStatus={streamStatus}
            />
          )}

          {streamStatus === 'completed' ? (
            <div className="rounded-md border border-emerald-900/50 bg-emerald-900/20 px-3 py-2 text-sm text-emerald-200">
              Workflow run completed.
            </div>
          ) : null}

          {streamStatus === 'error' && !runError ? (
            <div className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              Workflow run ended with an error. Check the event log below.
            </div>
          ) : null}

          {USE_API_MOCK ? (
            <div className="flex items-center justify-between rounded-md border border-white/5 bg-white/5 px-3 py-2 text-xs text-foreground/70">
              <span>Mock mode: emit a sample event stream.</span>
              <Button size="sm" onClick={handleSimulateStream} className="text-[11px]">
                Simulate stream
              </Button>
            </div>
          ) : null}

          <Sheet open={isTranscriptOpen} onOpenChange={setIsTranscriptOpen}>
            <div className="flex items-center justify-between gap-3">
              <div className="text-xs font-semibold uppercase tracking-wide text-foreground/60">Live events</div>
              <SheetTrigger asChild>
                <Button size="sm" variant="outline" disabled={!selectedRunId}>
                  View transcript
                </Button>
              </SheetTrigger>
            </div>
            {lastRunSummary ? (
              <div className="rounded-md border border-white/5 bg-white/5 px-3 py-2 text-xs text-foreground/80 flex flex-wrap gap-3">
                <InlineTag tone="default">
                  Workflow: {
                    workflows.find((w) => w.key === lastRunSummary.workflowKey)?.display_name ??
                    lastRunSummary.workflowKey
                  }
                </InlineTag>
                {lastRunSummary.runId ? <InlineTag tone="default">Run: {lastRunSummary.runId}</InlineTag> : null}
                {lastRunSummary.message ? (
                  <span className="truncate max-w-full text-foreground/60">Prompt: “{lastRunSummary.message}”</span>
                ) : null}
                {lastUpdated ? (
                  <span className="text-foreground/50">Last updated {new Date(lastUpdated).toLocaleTimeString()}</span>
                ) : null}
              </div>
            ) : null}
            <WorkflowStreamLog events={streamEvents} />
            <SheetContent side="right" className="sm:max-w-xl w-full">
              <SheetHeader>
                <SheetTitle>Run transcript</SheetTitle>
                <SheetDescription>Displays step outputs as a conversation.</SheetDescription>
              </SheetHeader>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                {selectedRunId ? <InlineTag tone="default">Run: {selectedRunId}</InlineTag> : null}
                {runDetailQuery.data?.workflow_key ? (
                  <InlineTag tone="default">
                    Workflow: {
                      workflows.find((w) => w.key === runDetailQuery.data?.workflow_key)?.display_name ??
                      runDetailQuery.data.workflow_key
                    }
                  </InlineTag>
                ) : null}
                {runDetailQuery.data?.status ? (
                  <InlineTag tone="default">Status: {runDetailQuery.data.status}</InlineTag>
                ) : null}
                {runDetailQuery.data?.conversation_id ? (
                  <InlineTag tone="default">Conversation: {runDetailQuery.data.conversation_id}</InlineTag>
                ) : null}
                {runDetailQuery.data?.status === 'running' ? (
                  <Button size="sm" variant="outline" onClick={handleCancelRun} disabled={cancelRunMutation.isPending}>
                    {cancelRunMutation.isPending ? 'Canceling…' : 'Cancel run'}
                  </Button>
                ) : null}
              </div>
              <div className="mt-4 h-[70vh] overflow-y-auto pr-2">
                <WorkflowRunConversation
                  run={runDetailQuery.data ?? null}
                  events={runEventsQuery.data ?? null}
                  isLoadingRun={runDetailQuery.isLoading}
                  isLoadingEvents={runEventsQuery.isLoading}
                />
              </div>
            </SheetContent>
          </Sheet>
        </GlassPanel>
      </div>

      <div className="space-y-4">
        <GlassPanel className="p-4 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-sm font-semibold">Run history</div>
              <p className="text-xs text-foreground/60">Recent runs for the selected workflow.</p>
            </div>
            <div className="flex items-center gap-2">
              <Select
                value={statusFilter}
                onValueChange={(value) =>
                  setStatusFilter(value as 'all' | 'running' | 'succeeded' | 'failed' | 'cancelled')
                }
              >
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
              <Button variant="ghost" size="sm" onClick={() => runsQuery.refetch()}>
                Refresh
              </Button>
            </div>
          </div>

          <WorkflowRunsList
            runs={runs}
            workflows={workflows}
            isLoading={isRunsInitialLoading}
            isFetchingMore={isLoadingMore}
            hasMore={Boolean(nextCursor)}
            onLoadMore={handleLoadMore}
            onSelectRun={handleSelectRun}
            selectedRunId={selectedRunId}
            onRefresh={() => runsQuery.refetch()}
          />
        </GlassPanel>
      </div>
    </div>
  );
}
