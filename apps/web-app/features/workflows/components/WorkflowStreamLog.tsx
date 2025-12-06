import { useEffect, useMemo, useRef } from 'react';

import { Badge } from '@/components/ui/badge';
import { CodeBlock } from '@/components/ui/ai/code-block';
import { Response } from '@/components/ui/ai/response';
import {
  Tool,
  ToolContent,
  ToolHeader,
  ToolInput,
  ToolOutput,
} from '@/components/ui/ai/tool';
import { renderToolOutput } from '@/components/ui/ai/renderToolOutput';
import { InlineTag } from '@/components/ui/foundation';
import { cn } from '@/lib/utils';
import type {
  StreamingWorkflowEvent,
  ToolCallPayload,
  UrlCitation as ApiUrlCitation,
  ContainerFileCitation as ApiContainerFileCitation,
  FileCitation as ApiFileCitation,
} from '@/lib/api/client/types.gen';
import type { Annotation } from '@/lib/chat/types';

interface WorkflowStreamLogProps {
  events: (StreamingWorkflowEvent & { receivedAt?: string })[];
}

const KIND_LABEL: Record<StreamingWorkflowEvent['kind'], string> = {
  lifecycle: 'Lifecycle',
  run_item_stream_event: 'Run Item',
  agent_updated_stream_event: 'Agent Update',
  raw_response_event: 'Response',
  usage: 'Usage',
  error: 'Error',
};

type ToolViewModel =
  | {
      label: string;
      state: 'input-streaming' | 'input-available' | 'output-available' | 'output-error';
      input?: unknown;
      output?: unknown;
      errorText?: string | null;
    }
  | null;

function mapAnnotations(
  anns: (ApiUrlCitation | ApiContainerFileCitation | ApiFileCitation)[] | undefined,
): Annotation[] | undefined {
  if (!anns?.length) return undefined;
  return anns.map((ann) => {
    if (ann.type === 'url_citation') {
      return ann as Annotation;
    }
    if (ann.type === 'container_file_citation') {
      return ann as Annotation;
    }
    return ann as Annotation;
  });
}

function mapToolCall(toolCall: ToolCallPayload | Record<string, unknown> | null | undefined): ToolViewModel {
  if (!toolCall || typeof toolCall !== 'object') return null;
  const anyCall = toolCall as ToolCallPayload;

  if (anyCall.web_search_call) {
    const status = anyCall.web_search_call.status === 'completed' ? 'output-available' : 'input-available';
    return {
      label: 'web_search',
      state: status,
      input: anyCall.web_search_call.action ?? null,
      output: anyCall.web_search_call.action ?? null,
    };
  }
  if (anyCall.code_interpreter_call) {
    const status =
      anyCall.code_interpreter_call.status === 'completed'
        ? 'output-available'
        : anyCall.code_interpreter_call.status === 'interpreting'
          ? 'input-available'
          : 'input-streaming';
    return {
      label: 'code_interpreter',
      state: status,
      input: anyCall.code_interpreter_call.code,
      output: {
        outputs: anyCall.code_interpreter_call.outputs,
        container_id: anyCall.code_interpreter_call.container_id,
        container_mode: anyCall.code_interpreter_call.container_mode,
        annotations: anyCall.code_interpreter_call.annotations,
      },
    };
  }
  if (anyCall.file_search_call) {
    const status =
      anyCall.file_search_call.status === 'completed'
        ? 'output-available'
        : anyCall.file_search_call.status === 'searching'
          ? 'input-available'
          : 'input-streaming';
    return {
      label: 'file_search',
      state: status,
      input: anyCall.file_search_call.queries,
      output: anyCall.file_search_call.results,
    };
  }
  if (anyCall.image_generation_call) {
    const status =
      anyCall.image_generation_call.status === 'completed'
        ? 'output-available'
        : anyCall.image_generation_call.status === 'partial_image'
          ? 'input-available'
          : 'input-streaming';
    return {
      label: 'image_generation',
      state: status,
      input: anyCall.image_generation_call.revised_prompt ?? null,
      output: [anyCall.image_generation_call],
    };
  }

    const fallbackType = (anyCall as { tool_type?: string }).tool_type ?? 'tool_call';
  return {
    label: fallbackType,
    state: 'input-available',
    input: anyCall,
  };
}

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
        const displayTime = evt.server_timestamp
          ? new Date(evt.server_timestamp).toLocaleTimeString()
          : evt.receivedAt
            ? new Date(evt.receivedAt).toLocaleTimeString()
            : null;
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
                  {evt.event ? (
                    <Badge variant="secondary" className="text-[11px] uppercase tracking-wide">
                      {evt.event}
                    </Badge>
                  ) : null}
                  {evt.raw_type ? (
                    <span className="text-[11px] uppercase tracking-wide text-foreground/50">{evt.raw_type}</span>
                  ) : null}
                  {evt.stage_name ? <InlineTag tone="default">Stage: {evt.stage_name}</InlineTag> : null}
                  {evt.parallel_group ? (
                    <InlineTag tone="default">Group: {evt.parallel_group}</InlineTag>
                  ) : null}
                  {evt.agent_used || evt.agent ? (
                    <InlineTag tone="default">Agent: {evt.agent_used ?? evt.agent}</InlineTag>
                  ) : null}
                </div>
                <div className="flex items-center gap-2 text-[11px] text-foreground/60">
                  {displayTime ? <span>{displayTime}</span> : null}
                  {isTerminal ? <span className="text-primary">Terminal</span> : null}
                </div>
              </div>

            {(() => {
              const content = evt.response_text ?? evt.text_delta;
              if (!content) return null;
              const annotations = mapAnnotations(
                evt.annotations as (ApiUrlCitation | ApiContainerFileCitation | ApiFileCitation)[] | undefined
              );
              return (
                <div className="mt-3">
                  <Response citations={annotations}>{content}</Response>
                </div>
              );
            })()}

            {evt.structured_output !== undefined && evt.structured_output !== null ? (
              <div className="mt-2">
                <CodeBlock
                  code={JSON.stringify(evt.structured_output, null, 2)}
                  language="json"
                />
              </div>
            ) : null}

            {evt.tool_call ? (
              (() => {
                const tool = mapToolCall(evt.tool_call as ToolCallPayload);
                if (!tool) return null;
                return (
                    <Tool>
                      <ToolHeader type={`tool-${tool.label}` as const} state={tool.state} />
                      <ToolContent>
                      {tool.input !== undefined ? <ToolInput input={tool.input} /> : null}
                      <ToolOutput
                        output={renderToolOutput(tool)}
                        errorText={tool.errorText ?? undefined}
                      />
                    </ToolContent>
                  </Tool>
                );
              })()
            ) : null}

          </div>
        );
      })}
    </div>
  );
}
