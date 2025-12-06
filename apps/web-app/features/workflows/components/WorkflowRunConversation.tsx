import { useMemo } from 'react';

import { Conversation, ConversationContent } from '@/components/ui/ai/conversation';
import { Message, MessageContent } from '@/components/ui/ai/message';
import { InlineTag } from '@/components/ui/foundation';
import { CodeBlock } from '@/components/ui/ai/code-block';
import { Response } from '@/components/ui/ai/response';
import type { WorkflowRunDetailView } from '@/lib/workflows/types';
import type { Annotation } from '@/lib/chat/types';
import type { ConversationEvents } from '@/types/conversations';
import { SkeletonPanel, EmptyState } from '@/components/ui/states';

interface WorkflowRunConversationProps {
  run: WorkflowRunDetailView | null;
  events: ConversationEvents | null | undefined;
  isLoadingRun?: boolean;
  isLoadingEvents?: boolean;
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
  events,
  isLoadingRun,
  isLoadingEvents,
}: WorkflowRunConversationProps) {
  const entries = useMemo<ConversationEntry[]>(() => {
    // Prefer conversation events when present
    if (events?.items?.length) {
      return events.items.map((item, idx) => ({
        id: `${item.response_id ?? idx}`,
        role: item.role === 'user' ? 'user' : 'assistant',
        content: item.content_text ?? item.reasoning_text ?? '[no content]',
        meta: compactMeta([
          item.run_item_type,
          item.run_item_name,
          item.tool_name ? `tool:${item.tool_name}` : null,
          item.agent ? `agent:${item.agent}` : null,
        ]),
        structured: item.call_output ?? item.call_arguments,
      }));
    }

    // Fallback to run detail steps
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
  }, [events, run]);

  if (isLoadingRun) {
    return <SkeletonPanel lines={8} />;
  }

  if (!run) {
    return <EmptyState title="Select a run" description="Choose a run to view its transcript." />;
  }

  if (isLoadingEvents && !entries.length) {
    return <SkeletonPanel lines={6} />;
  }

  return (
    <Conversation className="rounded-xl border border-white/5 bg-white/5">
      <ConversationContent className="space-y-4 p-4">
        {entries.length === 0 ? (
          <p className="text-sm text-foreground/60">No messages recorded for this run.</p>
        ) : (
          entries.map((entry) => (
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
          ))
        )}
      </ConversationContent>
    </Conversation>
  );
}

function compactMeta(values: (string | null | undefined)[]): string[] | undefined {
  const cleaned = values.filter(Boolean) as string[];
  return cleaned.length ? cleaned : undefined;
}
