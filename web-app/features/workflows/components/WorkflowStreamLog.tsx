import { useEffect, useMemo, useRef } from 'react';

import { Badge } from '@/components/ui/badge';
import { CodeBlock } from '@/components/ui/ai/code-block';
import { cn } from '@/lib/utils';
import type { StreamingWorkflowEvent } from '@/lib/api/client/types.gen';

interface WorkflowStreamLogProps {
  events: (StreamingWorkflowEvent & { receivedAt?: string })[];
}

const KIND_LABEL: Record<StreamingWorkflowEvent['kind'], string> = {
  lifecycle: 'Lifecycle',
  run_item: 'Run Item',
  agent_update: 'Agent Update',
  raw_response: 'Response',
  usage: 'Usage',
  error: 'Error',
};

export function WorkflowStreamLog({ events }: WorkflowStreamLogProps) {
  const grouped = useMemo(() => events, [events]);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    containerRef.current.scrollTo({ top: containerRef.current.scrollHeight, behavior: 'smooth' });
  }, [grouped.length]);

  if (grouped.length === 0) {
    return <p className="text-sm text-foreground/60">No events yet.</p>;
  }

  return (
    <div ref={containerRef} className="space-y-3 max-h-96 overflow-y-auto">
      {grouped.map((evt, idx) => {
        const label = KIND_LABEL[evt.kind] ?? evt.kind;
        const isTerminal = Boolean(evt.is_terminal);
        const receivedTime = evt.receivedAt ? new Date(evt.receivedAt).toLocaleTimeString() : null;
        return (
          <div
            key={`${evt.kind}-${evt.sequence_number ?? idx}-${idx}`}
            className={cn(
              'rounded-lg border border-white/5 bg-white/5 p-3 shadow-sm',
              isTerminal ? 'ring-1 ring-primary/40' : undefined,
            )}
            tabIndex={0}
          >
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <Badge variant={isTerminal ? 'default' : 'outline'}>{label}</Badge>
                {evt.raw_type ? (
                  <span className="text-[11px] uppercase tracking-wide text-foreground/50">{evt.raw_type}</span>
                ) : null}
              </div>
              <div className="flex items-center gap-2 text-[11px] text-foreground/60">
                {receivedTime ? <span>{receivedTime}</span> : null}
                {isTerminal ? <span className="text-primary">Terminal</span> : null}
              </div>
            </div>

            {evt.text_delta ? (
              <p className="mt-2 text-sm text-foreground">{evt.text_delta}</p>
            ) : null}

            {evt.response_text ? (
              <p className="mt-2 text-sm text-foreground">{String(evt.response_text)}</p>
            ) : null}

            {evt.structured_output !== undefined && evt.structured_output !== null ? (
              <div className="mt-2">
                <CodeBlock
                  code={JSON.stringify(evt.structured_output, null, 2)}
                  language="json"
                />
              </div>
            ) : null}

            {evt.payload ? (
              <div className="mt-2 text-xs text-foreground/70">
                <CodeBlock code={JSON.stringify(evt.payload, null, 2)} language="json" />
              </div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
