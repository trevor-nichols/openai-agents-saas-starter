'use client';

import { CodeBlock } from '@/components/ui/ai/code-block';
import { Response } from '@/components/ui/ai/response';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/states';
import { InlineTag } from '@/components/ui/foundation';
import type {
  MessageAttachment,
  PublicSseEvent,
  StreamingWorkflowEvent,
  WorkflowRunDetail,
} from '@/lib/api/client/types.gen';
import { useAttachmentResolver } from '@/hooks/useAttachmentResolver';
import { cn } from '@/lib/utils';

type FinalFromStream = {
  source: 'stream';
  status: string;
  responseText: string | null;
  structuredOutput: unknown | null;
  attachments: MessageAttachment[];
  usage: unknown | null;
};

type FinalFromRunDetail = {
  source: 'run_detail';
  status: string | null;
  responseText: string | null;
  structuredOutput: unknown | null;
  attachments: MessageAttachment[];
  usage: unknown | null;
  outputSchema: unknown | null;
};

type FinalViewModel = FinalFromStream | FinalFromRunDetail;

function isTerminalFinal(event: StreamingWorkflowEvent): event is Extract<StreamingWorkflowEvent, { kind: 'final' }> {
  return event.kind === 'final';
}

function toNonEmptyString(value: unknown): string | null {
  if (typeof value !== 'string') return null;
  const trimmed = value.trim();
  return trimmed.length ? trimmed : null;
}

function getLatestFinalFromReplay(replayEvents: PublicSseEvent[], runId?: string | null): FinalFromStream | null {
  return getLatestFinalFromEvents(replayEvents as StreamingWorkflowEvent[], runId);
}

function getLatestFinalFromEvents(
  events: StreamingWorkflowEvent[],
  runId?: string | null,
): FinalFromStream | null {
  for (let i = events.length - 1; i >= 0; i -= 1) {
    const evt = events[i];
    if (!evt) continue;
    if (!isTerminalFinal(evt)) continue;
    if (runId && evt.workflow?.workflow_run_id && evt.workflow.workflow_run_id !== runId) continue;

    return {
      source: 'stream',
      status: evt.final.status,
      responseText: toNonEmptyString(evt.final.response_text),
      structuredOutput: evt.final.structured_output ?? null,
      attachments: evt.final.attachments ?? [],
      usage: (evt.final as any).usage ?? null,
    };
  }
  return null;
}

export function WorkflowFinalOutput({
  selectedRunId,
  runDetail,
  replayEvents,
  streamEvents,
  className,
}: {
  selectedRunId: string | null;
  runDetail: WorkflowRunDetail | null;
  replayEvents: PublicSseEvent[] | null;
  streamEvents: StreamingWorkflowEvent[];
  className?: string;
}) {
  const { attachmentState, resolveAttachment } = useAttachmentResolver();
  const latestFinalFromReplay =
    selectedRunId && replayEvents?.length ? getLatestFinalFromReplay(replayEvents, selectedRunId) : null;
  const latestFinalFromStream = getLatestFinalFromEvents(streamEvents, selectedRunId);

  // Prefer ledger replay (authoritative), then run detail (history), then stream fallback.
  const model: FinalViewModel | null =
    latestFinalFromReplay ??
    (selectedRunId && runDetail && runDetail.workflow_run_id === selectedRunId
      ? {
          source: 'run_detail',
          status: runDetail.status ?? null,
          responseText: toNonEmptyString(runDetail.final_output_text),
          structuredOutput: runDetail.final_output_structured ?? null,
          attachments: [],
          usage: null,
          outputSchema: runDetail.output_schema ?? null,
        }
      : latestFinalFromStream);

  if (!model) {
    return (
      <div className={cn('p-4', className)}>
        <EmptyState
          title="No final output yet"
          description="Run a workflow or select a completed run to view its final output."
        />
      </div>
    );
  }

  const hasRenderableText = Boolean(model.responseText);
  const hasStructured = model.structuredOutput !== null && model.structuredOutput !== undefined;
  const hasAttachments = model.attachments.length > 0;

  return (
    <div className={cn('space-y-4 p-4', className)}>
      <div className="flex flex-wrap items-center gap-2">
        {selectedRunId ? <InlineTag tone="default">Run: {selectedRunId}</InlineTag> : null}
        {model.status ? <InlineTag tone="default">Status: {model.status}</InlineTag> : null}
        <InlineTag tone="default">Source: {model.source === 'stream' ? 'live stream' : 'history'}</InlineTag>
      </div>

      {hasRenderableText ? (
        <div className="rounded-lg border border-white/5 bg-white/5 p-4">
          <div className="text-xs font-semibold uppercase tracking-wide text-foreground/60">Final output</div>
          <div className="mt-3">
            <Response parseIncompleteMarkdown={false}>{model.responseText}</Response>
          </div>
        </div>
      ) : null}

      {hasStructured ? (
        <div className="rounded-lg border border-white/5 bg-white/5 p-4">
          <div className="text-xs font-semibold uppercase tracking-wide text-foreground/60">Structured output</div>
          <div className="mt-3">
            <CodeBlock code={JSON.stringify(model.structuredOutput, null, 2)} language="json" />
          </div>
        </div>
      ) : null}

      {'outputSchema' in model && model.outputSchema ? (
        <div className="rounded-lg border border-white/5 bg-white/5 p-4">
          <div className="text-xs font-semibold uppercase tracking-wide text-foreground/60">Declared output schema</div>
          <div className="mt-3">
            <CodeBlock code={JSON.stringify(model.outputSchema, null, 2)} language="json" />
          </div>
        </div>
      ) : null}

      {hasAttachments ? (
        <div className="rounded-lg border border-white/5 bg-white/5 p-4">
          <div className="text-xs font-semibold uppercase tracking-wide text-foreground/60">Attachments</div>
          <div className="mt-3 space-y-2">
            {model.attachments.map((att) => (
              <div
                key={att.object_id}
                className="flex items-center justify-between gap-3 rounded-md border border-white/10 bg-white/5 px-3 py-2 text-xs"
              >
                <div className="min-w-0">
                  <div className="truncate font-medium text-foreground" title={att.filename}>
                    {att.filename}
                  </div>
                  <div className="truncate text-foreground/60">
                    {att.mime_type ?? 'file'}
                  </div>
                </div>

                {(() => {
                  const resolved = attachmentState[att.object_id];
                  const url = att.url ?? resolved?.url;
                  if (url) {
                    return (
                      <a
                        className="shrink-0 font-semibold text-primary hover:underline"
                        href={url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Download
                      </a>
                    );
                  }

                  const loading = Boolean(resolved?.loading);
                  const errorText = resolved?.error;
                  return (
                    <div className="flex items-center gap-2">
                      {errorText ? <span className="text-destructive/80">{errorText}</span> : null}
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        className="h-7 text-[10px]"
                        disabled={loading}
                        onClick={() => resolveAttachment(att.object_id)}
                      >
                        {loading ? 'Fetching…' : 'Get link'}
                      </Button>
                    </div>
                  );
                })()}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {!hasRenderableText && !hasStructured && !hasAttachments ? (
        <div className="rounded-lg border border-white/5 bg-white/5 p-4 text-sm text-foreground/70">
          Final output is empty for this run.
        </div>
      ) : null}
    </div>
  );
}
