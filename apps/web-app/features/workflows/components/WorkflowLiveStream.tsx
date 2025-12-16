'use client';

import { useMemo } from 'react';

import { Badge } from '@/components/ui/badge';
import { InlineTag } from '@/components/ui/foundation';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Response } from '@/components/ui/ai/response';
import {
  Tool,
  ToolContent,
  ToolHeader,
  ToolInput,
  ToolOutput,
} from '@/components/ui/ai/tool';
import { renderToolOutput } from '@/components/ui/ai/renderToolOutput';
import { cn } from '@/lib/utils';
import type { StreamingWorkflowEvent } from '@/lib/api/client/types.gen';
import { buildWorkflowLiveTranscript } from '@/lib/workflows/liveStreamTranscript';

type StreamEventWithMeta = StreamingWorkflowEvent & { receivedAt?: string };

export function WorkflowLiveStream({
  events,
  className,
}: {
  events: StreamEventWithMeta[];
  className?: string;
}) {
  const transcript = useMemo(() => buildWorkflowLiveTranscript(events), [events]);

  if (transcript.length === 0) {
    return <p className={cn('text-sm text-foreground/60', className)}>Waiting for workflow output…</p>;
  }

  return (
    <div className={cn('space-y-3', className)}>
      {transcript.map((segment) => {
        const workflow = segment.workflow ?? null;
        const headerLabel = workflow?.step_name ?? workflow?.stage_name ?? 'Workflow';
        const reasoningText = segment.reasoningSummaryText;

        return (
          <div
            key={segment.key}
            className="rounded-lg border border-white/5 bg-white/5 p-3 shadow-sm"
          >
            <div className="flex items-center justify-between gap-2">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="outline">{headerLabel}</Badge>
                {workflow?.stage_name ? <InlineTag tone="default">Stage: {workflow.stage_name}</InlineTag> : null}
                {workflow?.step_name ? <InlineTag tone="default">Step: {workflow.step_name}</InlineTag> : null}
                {workflow?.parallel_group ? (
                  <InlineTag tone="default">Group: {workflow.parallel_group}</InlineTag>
                ) : null}
                {typeof workflow?.branch_index === 'number' ? (
                  <InlineTag tone="default">Branch: {workflow.branch_index}</InlineTag>
                ) : null}
                {segment.agent ? <InlineTag tone="default">Agent: {segment.agent}</InlineTag> : null}
              </div>
              {segment.responseId ? (
                <span className="text-[11px] text-foreground/60 font-mono">
                  {segment.responseId.slice(-8)}
                </span>
              ) : null}
            </div>

            {reasoningText ? (
              <Collapsible>
                <div className="mt-3 flex items-center justify-between">
                  <div className="text-[11px] font-semibold uppercase tracking-wide text-foreground/60">
                    Thinking
                  </div>
                  <CollapsibleTrigger className="text-[11px] text-foreground/70 underline underline-offset-4">
                    Show
                  </CollapsibleTrigger>
                </div>
                <CollapsibleContent className="mt-2 rounded-md border border-white/10 bg-white/5 p-2">
                  <Response>{reasoningText}</Response>
                </CollapsibleContent>
              </Collapsible>
            ) : null}

            <div className="mt-3 space-y-3">
              {segment.items.map((item) => {
                if (item.kind === 'tool') {
                  const tool = item.tool;
                  return (
                    <Tool key={`tool:${item.itemId}`} defaultOpen={tool.state !== 'output-available'}>
                      <ToolHeader type={`tool-${tool.label}` as const} state={tool.state} />
                      <ToolContent>
                        {tool.input !== undefined ? <ToolInput input={tool.input} /> : null}
                        <ToolOutput output={renderToolOutput({ label: tool.label, output: tool.output })} errorText={tool.errorText ?? undefined} />
                      </ToolContent>
                    </Tool>
                  );
                }

                if (item.kind === 'refusal') {
                  return (
                    <div key={`refusal:${item.itemId}`} className="rounded-md border border-destructive/40 bg-destructive/10 p-2">
                      <Response>{item.text}</Response>
                    </div>
                  );
                }

                return (
                  <div key={`msg:${item.itemId}`} className="rounded-md border border-white/10 bg-white/5 p-2">
                    <Response>{item.text}</Response>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
