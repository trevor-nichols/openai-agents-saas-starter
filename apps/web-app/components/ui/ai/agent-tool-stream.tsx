'use client';

import { cn } from '@/lib/utils';
import type { ComponentProps } from 'react';
import { Response } from './response';
import type { AgentToolStream } from '@/lib/streams/publicSseV1/agentToolStreams';

export type AgentToolStreamProps = ComponentProps<'div'> & {
  stream: AgentToolStream;
  isStreaming?: boolean;
};

export function AgentToolStream({
  stream,
  isStreaming = false,
  className,
  ...props
}: AgentToolStreamProps) {
  const text = stream.text?.trim();
  if (!text) return null;

  const displayText = isStreaming ? `${text}▋` : text;

  return (
    <div className={cn('border-t bg-muted/20 px-3 py-2', className)} {...props}>
      <div className="mb-2 flex items-center gap-2">
        <span className="font-semibold text-[9px] text-muted-foreground uppercase tracking-wider">
          Agent stream
        </span>
        {stream.agent ? (
          <span className="rounded-full border border-border/60 px-2 py-0.5 text-[10px] text-foreground/70">
            {stream.agent}
          </span>
        ) : null}
      </div>
      <div className="rounded-lg border bg-background p-3 text-sm text-foreground/90">
        <Response citations={stream.citations}>{displayText}</Response>
      </div>
    </div>
  );
}
