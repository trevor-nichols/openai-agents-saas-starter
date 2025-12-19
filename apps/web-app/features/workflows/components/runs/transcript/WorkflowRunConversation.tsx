import { useMemo } from 'react';

import { Conversation, ConversationContent } from '@/components/ui/ai/conversation';
import { Message, MessageContent } from '@/components/ui/ai/message';
import { InlineTag } from '@/components/ui/foundation';
import { CodeBlock } from '@/components/ui/ai/code-block';
import { Response } from '@/components/ui/ai/response';
import { cn } from '@/lib/utils';
import type { WorkflowRunDetailView } from '@/lib/workflows/types';
import type { Annotation } from '@/lib/chat/types';
import { SkeletonPanel, EmptyState } from '@/components/ui/states';
import type { PublicSseEvent, StreamingWorkflowEvent } from '@/lib/api/client/types.gen';
import { WorkflowLiveStream } from '../streaming/WorkflowLiveStream';

interface WorkflowRunConversationProps {
  run: WorkflowRunDetailView | null;
  replayEvents: PublicSseEvent[] | null | undefined;
  isLoadingRun?: boolean;
  isLoadingReplay?: boolean;
  className?: string;
}

type ConversationEntry = {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  meta?: string[];
  structured?: unknown;
  citations?: Annotation[] | null;
};

export function WorkflowRunConversation({
  run,
  replayEvents,
  isLoadingRun,
  isLoadingReplay,
  className,
}: WorkflowRunConversationProps) {
  const entries = useMemo<ConversationEntry[]>(() => {
    // Fallback to run detail steps when no replay ledger exists (or hasn't loaded yet).
    const base: ConversationEntry[] = [];
    if (!run) return base;

    if (run.request_message) {
      base.push({
        id: 'request',
        role: 'user',
        content: run.request_message,
      });
    }
    run.steps.forEach((step, idx) => {
      base.push({
        id: step.response_id ?? `${step.name}-${idx}`,
        role: 'assistant',
        content: step.response_text ?? '[no response text]',
        meta: compactMeta([
          step.name,
          `agent:${step.agent_key}`,
          step.stage_name ? `stage:${step.stage_name}` : null,
          step.parallel_group ? `group:${step.parallel_group}` : null,
        ]),
        structured: step.structured_output,
      });
    });
    return base;
  }, [run]);

  if (isLoadingRun) {
    return <SkeletonPanel lines={8} />;
  }

  if (!run) {
    return <EmptyState title="Select a run" description="Choose a run to view its transcript." />;
  }

  if (isLoadingReplay && !replayEvents?.length && !entries.length) {
    return <SkeletonPanel lines={6} />;
  }

  return (
    <Conversation className={cn('rounded-xl border border-white/5 bg-white/5', className)}>
      <ConversationContent className="space-y-4 p-4">
        {run.request_message ? (
          <Message from="user">
            <MessageContent>
              <div className="flex flex-wrap items-center gap-2">
                <InlineTag tone="positive">User</InlineTag>
                <InlineTag tone="default">Prompt</InlineTag>
              </div>
              <div className="mt-2">
                <Response parseIncompleteMarkdown={false}>{run.request_message}</Response>
              </div>
            </MessageContent>
          </Message>
        ) : null}

        {replayEvents?.length ? (
          <WorkflowLiveStream
            events={replayEvents as StreamingWorkflowEvent[]}
            className="mt-2"
          />
        ) : entries.length ? (
          <div className="space-y-4">
            <div className="text-xs text-foreground/60">
              Replay stream is not available for this run; showing step summaries instead.
            </div>
            {entries.map((entry) => (
              <Message key={entry.id} from={entry.role}>
                <MessageContent>
                  <div className="flex flex-wrap items-center gap-2">
                    <InlineTag tone={entry.role === 'user' ? 'positive' : 'default'}>
                      {entry.role === 'user' ? 'User' : 'Workflow'}
                    </InlineTag>
                    {entry.meta?.map((m) => (
                      <InlineTag key={m} tone="default">
                        {m}
                      </InlineTag>
                    ))}
                  </div>
                  <div className="mt-2">
                    <Response citations={entry.citations}>{entry.content}</Response>
                  </div>
                  {entry.structured ? (
                    <div className="mt-2">
                      <CodeBlock code={JSON.stringify(entry.structured, null, 2)} language="json" />
                    </div>
                  ) : null}
                </MessageContent>
              </Message>
            ))}
          </div>
        ) : (
          <p className="text-sm text-foreground/60">No messages recorded for this run.</p>
        )}
      </ConversationContent>
    </Conversation>
  );
}

function compactMeta(values: (string | null | undefined)[]): string[] | undefined {
  const cleaned = values.filter(Boolean) as string[];
  return cleaned.length ? cleaned : undefined;
}
