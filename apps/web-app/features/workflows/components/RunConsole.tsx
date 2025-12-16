'use client';

import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { InlineTag } from '@/components/ui/foundation';
import { GlassPanel } from '@/components/ui/foundation';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import type {
  LocationHint,
  StreamingWorkflowEvent,
  WorkflowRunDetail,
  WorkflowSummary,
} from '@/lib/api/client/types.gen';
import type { ConversationEvents } from '@/types/conversations';
import type { StreamStatus } from '../constants';
import { WorkflowRunPanel } from './WorkflowRunPanel';
import { WorkflowStreamLog } from './WorkflowStreamLog';
import { WorkflowLiveStream } from './WorkflowLiveStream';
import { WorkflowRunConversation } from './WorkflowRunConversation';
import { WorkflowRunDeleteButton } from './WorkflowRunDeleteButton';

type StreamEventWithMeta = StreamingWorkflowEvent & { receivedAt: string };

type RunSummary = {
  workflowKey: string;
  runId?: string | null;
  message?: string;
};

type Props = {
  workflows: WorkflowSummary[];
  selectedWorkflowKey: string | null;
  onRun: (input: { workflowKey: string; message: string; shareLocation?: boolean; location?: LocationHint | null }) => Promise<void>;
  isRunning: boolean;
  isLoadingWorkflows: boolean;
  runError: string | null;
  streamStatus: StreamStatus;
  isMockMode: boolean;
  onSimulate?: () => void;
  streamEvents: StreamEventWithMeta[];
  lastRunSummary: RunSummary | null;
  lastUpdated: string | null;
  selectedRunId: string | null;
  runDetail: WorkflowRunDetail | null;
  runEvents: ConversationEvents | null | undefined;
  isLoadingRun: boolean;
  isLoadingEvents: boolean;
  onCancelRun: () => void;
  cancelPending: boolean;
  onDeleteRun: (runId: string, conversationId?: string | null) => void;
  deletingRunId: string | null;
};

export function RunConsole({
  workflows,
  selectedWorkflowKey,
  onRun,
  isRunning,
  isLoadingWorkflows,
  runError,
  streamStatus,
  isMockMode,
  onSimulate,
  streamEvents,
  lastRunSummary,
  lastUpdated,
  selectedRunId,
  runDetail,
  runEvents,
  isLoadingRun,
  isLoadingEvents,
  onCancelRun,
  cancelPending,
  onDeleteRun,
  deletingRunId,
}: Props) {
  const [isTranscriptOpen, setIsTranscriptOpen] = useState(false);
  const [debugOpen, setDebugOpen] = useState(false);
  const transcriptOpen = isTranscriptOpen && Boolean(selectedRunId);
  const handleTranscriptToggle = (open: boolean) => {
    if (!open) {
      setIsTranscriptOpen(false);
      return;
    }
    if (selectedRunId) {
      setIsTranscriptOpen(true);
    }
  };

  return (
    <GlassPanel className="space-y-4 p-4">
      <WorkflowRunPanel
        selectedKey={selectedWorkflowKey}
        onRun={onRun}
        isRunning={isRunning}
        runError={runError}
        isLoadingWorkflows={isLoadingWorkflows}
        streamStatus={streamStatus}
      />

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

      {isMockMode ? (
        <div className="flex items-center justify-between rounded-md border border-white/5 bg-white/5 px-3 py-2 text-xs text-foreground/70">
          <span>Mock mode: emit a sample event stream.</span>
          <Button size="sm" onClick={onSimulate} className="text-[11px]">
            Simulate stream
          </Button>
        </div>
      ) : null}

      <Sheet open={transcriptOpen} onOpenChange={handleTranscriptToggle}>
        <div className="flex items-center justify-between gap-3">
          <div className="text-xs font-semibold uppercase tracking-wide text-foreground/60">Live events</div>
          <SheetTrigger asChild>
            <Button size="sm" variant="outline" disabled={!selectedRunId}>
              View transcript
            </Button>
          </SheetTrigger>
        </div>
        {lastRunSummary ? (
          <div className="flex flex-wrap gap-3 rounded-md border border-white/5 bg-white/5 px-3 py-2 text-xs text-foreground/80">
            <InlineTag tone="default">
              Workflow: {workflows.find((w) => w.key === lastRunSummary.workflowKey)?.display_name ?? lastRunSummary.workflowKey}
            </InlineTag>
            {lastRunSummary.runId ? <InlineTag tone="default">Run: {lastRunSummary.runId}</InlineTag> : null}
            {lastRunSummary.message ? (
              <span className="max-w-full truncate text-foreground/60">Prompt: “{lastRunSummary.message}”</span>
            ) : null}
            {lastUpdated ? (
              <span className="text-foreground/50">Last updated {new Date(lastUpdated).toLocaleTimeString()}</span>
            ) : null}
          </div>
        ) : null}
        <WorkflowLiveStream events={streamEvents} />

        <Collapsible open={debugOpen} onOpenChange={setDebugOpen}>
          <div className="mt-3 flex items-center justify-between">
            <div className="text-xs font-semibold uppercase tracking-wide text-foreground/60">Debug events</div>
            <CollapsibleTrigger asChild>
              <Button size="sm" variant="ghost" className="h-7 text-xs">
                {debugOpen ? 'Hide' : 'Show'}
              </Button>
            </CollapsibleTrigger>
          </div>
          <CollapsibleContent className="mt-3">
            <WorkflowStreamLog events={streamEvents} />
          </CollapsibleContent>
        </Collapsible>
        <SheetContent side="right" className="flex w-full flex-col overflow-hidden sm:max-w-xl">
          <SheetHeader>
            <SheetTitle>Run transcript</SheetTitle>
            <SheetDescription>Displays step outputs as a conversation.</SheetDescription>
          </SheetHeader>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            {selectedRunId ? <InlineTag tone="default">Run: {selectedRunId}</InlineTag> : null}
            {runDetail?.workflow_key ? (
              <InlineTag tone="default">
                Workflow: {workflows.find((w) => w.key === runDetail.workflow_key)?.display_name ?? runDetail.workflow_key}
              </InlineTag>
            ) : null}
            {runDetail?.status ? <InlineTag tone="default">Status: {runDetail.status}</InlineTag> : null}
            {runDetail?.conversation_id ? <InlineTag tone="default">Conversation: {runDetail.conversation_id}</InlineTag> : null}
            {runDetail?.status === 'running' ? (
              <Button size="sm" variant="outline" onClick={onCancelRun} disabled={cancelPending}>
                {cancelPending ? 'Canceling…' : 'Cancel run'}
              </Button>
            ) : null}
            {runDetail ? (
              <WorkflowRunDeleteButton
                onConfirm={() => onDeleteRun(runDetail.workflow_run_id, runDetail.conversation_id ?? null)}
                pending={deletingRunId === runDetail.workflow_run_id}
                tooltip="Delete run"
              />
            ) : null}
          </div>
          <div className="mt-4 flex min-h-0 flex-1 pr-2">
            <WorkflowRunConversation
              run={runDetail ?? null}
              events={runEvents ?? null}
              isLoadingRun={isLoadingRun}
              isLoadingEvents={isLoadingEvents}
              className="min-h-0 flex-1"
            />
          </div>
        </SheetContent>
      </Sheet>
    </GlassPanel>
  );
}
