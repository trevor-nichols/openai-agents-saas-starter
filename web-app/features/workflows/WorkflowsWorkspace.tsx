'use client';

import { useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
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

export function WorkflowsWorkspace() {
  const { data: workflows = [], isLoading, isError } = useWorkflowsQuery();
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [streamEvents, setStreamEvents] = useState<StreamingWorkflowEvent[]>([]);
  const [runError, setRunError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);

  const handleRun = async (input: {
    workflowKey: string;
    message: string;
    conversationId?: string | null;
    shareLocation?: boolean;
  }) => {
    setRunError(null);
    setStreamEvents([]);
    setIsStreaming(true);
    try {
      const body: WorkflowRunRequestBody = {
        message: input.message,
        conversation_id: input.conversationId ?? undefined,
        share_location: input.shareLocation ?? null,
      };

      for await (const evt of streamWorkflowRun(input.workflowKey, body)) {
        setStreamEvents((prev) => [...prev, evt]);
        if (evt.is_terminal) {
          break;
        }
      }
    } catch (error) {
      setRunError(error instanceof Error ? error.message : 'Failed to run workflow');
    } finally {
      setIsStreaming(false);
    }
  };

  const handleSimulateStream = async () => {
    setRunError(null);
    setStreamEvents([]);
    const runId = `mock_run_${Date.now()}`;
    for await (const evt of mockWorkflowStream(runId)) {
      setStreamEvents((prev) => [...prev, evt]);
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
          />
        )}

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
          <WorkflowStreamLog events={streamEvents} />
        </div>
      </GlassPanel>
    </div>
  );
}
