'use client';

import { memo } from 'react';

import { cn } from '@/lib/utils';
import type { ReasoningPart } from '@/lib/streams/publicSseV1/reasoningParts';
import { Reasoning, ReasoningContent, ReasoningTrigger } from '@/components/ui/ai/reasoning';
import { Response } from '@/components/ui/ai/response';

export interface ReasoningPartsProps {
  parts: ReasoningPart[];
  isStreaming: boolean;
  defaultOpen?: boolean;
  className?: string;
}

export const ReasoningParts = memo(({ parts, isStreaming, defaultOpen, className }: ReasoningPartsProps) => {
  const visible = parts.filter((part) => part.text.trim().length > 0);
  if (visible.length === 0) return null;

  return (
    <Reasoning
      isStreaming={isStreaming}
      defaultOpen={defaultOpen ?? true}
      className={cn('rounded-lg border border-white/5 bg-white/5 px-4 py-3', className)}
    >
      <ReasoningTrigger title="Reasoning" />
      <ReasoningContent>
        <ul className="grid gap-2">
          {visible.map((part, idx) => {
            const showCursor = isStreaming && idx === visible.length - 1 && part.status === 'streaming';
            const text = showCursor ? `${part.text}▋` : part.text;
            return (
              <li key={part.summaryIndex} className="flex items-start gap-2">
                <span className="mt-[6px] size-1.5 shrink-0 rounded-full bg-foreground/40" />
                <Response className="flex-1">{text}</Response>
              </li>
            );
          })}
        </ul>
      </ReasoningContent>
    </Reasoning>
  );
});

ReasoningParts.displayName = 'ReasoningParts';

