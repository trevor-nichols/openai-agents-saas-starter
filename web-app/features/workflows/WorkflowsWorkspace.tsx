'use client';

import { useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { InlineTag } from '@/components/ui/foundation';
import { GlassPanel, SectionHeader } from '@/components/ui/foundation';
import { ErrorState, SkeletonPanel } from '@/components/ui/states';
import { useWorkflowsQuery } from '@/lib/queries/workflows';
import type { StreamingWorkflowEvent, WorkflowRunRequestBody } from '@/lib/api/client/types.gen';
import { USE_API_MOCK } from '@/lib/config';
import { mockWorkflowStream } from '@/lib/workflows/mock';
import { streamWorkflowRun } from '@/lib/api/workflows';
import { WorkflowList } from './components/WorkflowList';
import { WorkflowRunPanel } from './components/WorkflowRunPanel';
import { WorkflowStreamLog } from './components/WorkflowStreamLog';

type StreamEventWithMeta = StreamingWorkflowEvent & { receivedAt: string };

type StreamStatus = 'idle' | 'connecting' | 'streaming' | 'completed' | 'error';

export function WorkflowsWorkspace() {
  const { data: workflows = [], isLoading, isError } = useWorkflowsQuery();
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [streamEvents, setStreamEvents] = useState<StreamEventWithMeta[]>([]);
  const [runError, setRunError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamStatus, setStreamStatus] = useState<StreamStatus>('idle');
  const [lastRunSummary, setLastRunSummary] = useState<{
    workflowKey: string;
    runId?: string | null;
    message?: string;
  } | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const handleRun = async (input: {
    workflowKey: string;
    message: string;
    conversationId?: string | null;
    shareLocation?: boolean;
  }) => {
    setRunError(null);
    setStreamEvents([]);
    setIsStreaming(true);
    setStreamStatus('connecting');
    setLastRunSummary({ workflowKey: input.workflowKey, runId: null, message: input.message });
    setLastUpdated(null);
    try {
      const body: WorkflowRunRequestBody = {
        message: input.message,
        conversation_id: input.conversationId ?? undefined,
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

  const initialKey = useMemo(() => workflows[0]?.key ?? null, [workflows]);
  const effectiveSelectedKey = selectedKey ?? initialKey;

  if (isError) {
    return <ErrorState title="Unable to load workflows" />;
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[320px_minmax(0,1fr)]">
      <div className="space-y-3">
        <SectionHeader title="Workflows" description="Run multi-step workflows with streaming output." />
        <GlassPanel className="p-4">
          <WorkflowList
            items={workflows}
            isLoading={isLoading}
            selectedKey={effectiveSelectedKey}
            onSelect={setSelectedKey}
          />
        </GlassPanel>
      </div>

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

        <div className="space-y-2">
          <div className="text-xs font-semibold uppercase tracking-wide text-foreground/60">Live events</div>
          {lastRunSummary ? (
            <div className="rounded-md border border-white/5 bg-white/5 px-3 py-2 text-xs text-foreground/80 flex flex-wrap gap-3">
              <InlineTag tone="default">Workflow: {lastRunSummary.workflowKey}</InlineTag>
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
        </div>
      </GlassPanel>
    </div>
  );
}
