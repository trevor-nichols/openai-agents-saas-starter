import { useMemo } from 'react';

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
import type { StreamingWorkflowEvent } from '@/lib/api/client/types.gen';

interface WorkflowStreamLogProps {
  events: (StreamingWorkflowEvent & { receivedAt?: string })[];
}

type KnownKind = NonNullable<StreamingWorkflowEvent['kind']>;

const KIND_LABEL: Record<KnownKind, string> = {
  lifecycle: 'Lifecycle',
  'message.delta': 'Message',
  'message.citation': 'Citation',
  'reasoning_summary.delta': 'Reasoning Summary',
  'refusal.delta': 'Refusal',
  'refusal.done': 'Refusal',
  'tool.status': 'Tool Status',
  'tool.arguments.delta': 'Tool Args',
  'tool.arguments.done': 'Tool Args',
  'tool.code.delta': 'Tool Code',
  'tool.code.done': 'Tool Code',
  'tool.output': 'Tool Output',
  'chunk.delta': 'Chunk',
  'chunk.done': 'Chunk',
  error: 'Error',
  final: 'Final',
};

type ToolViewModel = {
  label: string;
  state: 'input-streaming' | 'input-available' | 'output-available' | 'output-error';
  input?: unknown;
  output?: unknown;
  errorText?: string | null;
};

function toolStateFromStatus(status: string): ToolViewModel['state'] {
  if (status === 'completed') return 'output-available';
  if (status === 'failed') return 'output-error';
  return 'input-available';
}

function mapTool(tool: Extract<StreamingWorkflowEvent, { kind?: 'tool.status' }>['tool']): ToolViewModel {
  if (tool.tool_type === 'web_search') {
    return {
      label: 'web_search',
      state: toolStateFromStatus(tool.status),
      input: tool.query ?? undefined,
      output: tool.sources ?? undefined,
    };
  }

  if (tool.tool_type === 'file_search') {
    return {
      label: 'file_search',
      state: toolStateFromStatus(tool.status),
      input: tool.queries ?? undefined,
      output: tool.results ?? undefined,
    };
  }

  if (tool.tool_type === 'code_interpreter') {
    return {
      label: 'code_interpreter',
      state: toolStateFromStatus(tool.status),
      input: {
        container_id: tool.container_id ?? null,
        container_mode: tool.container_mode ?? null,
      },
    };
  }

  if (tool.tool_type === 'image_generation') {
    return {
      label: 'image_generation',
      state: toolStateFromStatus(tool.status),
      input: {
        revised_prompt: tool.revised_prompt ?? null,
        format: tool.format ?? null,
        size: tool.size ?? null,
        quality: tool.quality ?? null,
        background: tool.background ?? null,
        partial_image_index: tool.partial_image_index ?? null,
      },
    };
  }

  if (tool.tool_type === 'function') {
    return {
      label: tool.name,
      state: toolStateFromStatus(tool.status),
      input: tool.arguments_json ?? tool.arguments_text ?? undefined,
      output: tool.output ?? undefined,
      errorText: tool.status === 'failed' ? 'Tool failed' : undefined,
    };
  }

  return {
    label: tool.tool_name,
    state: toolStateFromStatus(tool.status),
    input: {
      server_label: tool.server_label ?? null,
      arguments: tool.arguments_json ?? tool.arguments_text ?? null,
    },
    output: tool.output ?? undefined,
    errorText: tool.status === 'failed' ? 'Tool failed' : undefined,
  };
}

export function WorkflowStreamLog({ events }: WorkflowStreamLogProps) {
  const grouped = useMemo(() => events, [events]);

  if (grouped.length === 0) {
    return <p className="text-sm text-foreground/60">No events yet.</p>;
  }

  return (
    <div className="space-y-3">
      {grouped.map((evt, idx) => {
        const kind = evt.kind;
        const isTerminal = kind === 'final' || kind === 'error';
        const label = kind ? (KIND_LABEL[kind] ?? kind) : 'Unknown';

        const displayTime = evt.server_timestamp
          ? new Date(evt.server_timestamp).toLocaleTimeString()
          : evt.receivedAt
            ? new Date(evt.receivedAt).toLocaleTimeString()
            : null;

        const workflow = evt.workflow ?? null;

        return (
          <div
            key={`${evt.stream_id}-${evt.event_id}-${idx}`}
            className={cn(
              'rounded-lg border border-white/5 bg-white/5 p-3 shadow-sm',
              isTerminal ? 'ring-1 ring-primary/40' : undefined,
            )}
            tabIndex={0}
          >
            <div className="flex items-center justify-between gap-2">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={isTerminal ? 'default' : 'outline'}>{label}</Badge>

                {workflow?.stage_name ? <InlineTag tone="default">Stage: {workflow.stage_name}</InlineTag> : null}
                {workflow?.step_name ? <InlineTag tone="default">Step: {workflow.step_name}</InlineTag> : null}
                {workflow?.parallel_group ? (
                  <InlineTag tone="default">Group: {workflow.parallel_group}</InlineTag>
                ) : null}
                {typeof workflow?.branch_index === 'number' ? (
                  <InlineTag tone="default">Branch: {workflow.branch_index}</InlineTag>
                ) : null}
                {workflow?.workflow_run_id ? (
                  <InlineTag tone="default">Run: {workflow.workflow_run_id.slice(-8)}</InlineTag>
                ) : null}
                {evt.agent ? <InlineTag tone="default">Agent: {evt.agent}</InlineTag> : null}
              </div>

              <div className="flex items-center gap-2 text-[11px] text-foreground/60">
                {displayTime ? <span>{displayTime}</span> : null}
                {isTerminal ? <span className="text-primary">Terminal</span> : null}
              </div>
            </div>

            {(() => {
              switch (evt.kind) {
                case 'lifecycle':
                  return (
                    <div className="mt-3">
                      <CodeBlock
                        code={JSON.stringify(
                          { status: evt.status, reason: evt.reason ?? null },
                          null,
                          2,
                        )}
                        language="json"
                      />
                    </div>
                  );
                case 'message.delta':
                  return (
                    <div className="mt-3">
                      <Response>{evt.delta}</Response>
                    </div>
                  );
                case 'message.citation':
                  return (
                    <div className="mt-3">
                      <CodeBlock code={JSON.stringify(evt.citation, null, 2)} language="json" />
                    </div>
                  );
                case 'reasoning_summary.delta':
                  return (
                    <div className="mt-3">
                      <Response>{evt.delta}</Response>
                    </div>
                  );
                case 'refusal.delta':
                  return (
                    <div className="mt-3">
                      <Response>{evt.delta}</Response>
                    </div>
                  );
                case 'refusal.done':
                  return (
                    <div className="mt-3">
                      <Response>{evt.refusal_text}</Response>
                    </div>
                  );
                case 'tool.status': {
                  const tool = mapTool(evt.tool);
                  return (
                    <div className="mt-3">
                      <Tool defaultOpen={tool.state !== 'output-available'}>
                        <ToolHeader type={`tool-${tool.label}` as const} state={tool.state} />
                        <ToolContent>
                          {tool.input !== undefined ? <ToolInput input={tool.input} /> : null}
                          <ToolOutput
                            output={renderToolOutput(tool)}
                            errorText={tool.errorText ?? undefined}
                          />
                        </ToolContent>
                      </Tool>
                    </div>
                  );
                }
                case 'tool.arguments.delta':
                  return (
                    <div className="mt-3">
                      <CodeBlock
                        code={JSON.stringify(
                          {
                            tool_call_id: evt.tool_call_id,
                            tool_type: evt.tool_type,
                            tool_name: evt.tool_name,
                            delta: evt.delta,
                          },
                          null,
                          2,
                        )}
                        language="json"
                      />
                    </div>
                  );
                case 'tool.arguments.done':
                  return (
                    <div className="mt-3">
                      <CodeBlock
                        code={JSON.stringify(
                          {
                            tool_call_id: evt.tool_call_id,
                            tool_type: evt.tool_type,
                            tool_name: evt.tool_name,
                            arguments_text: evt.arguments_text,
                            arguments_json: evt.arguments_json ?? null,
                          },
                          null,
                          2,
                        )}
                        language="json"
                      />
                    </div>
                  );
                case 'tool.code.delta':
                  return (
                    <div className="mt-3">
                      <CodeBlock code={evt.delta} language="python" />
                    </div>
                  );
                case 'tool.code.done':
                  return (
                    <div className="mt-3">
                      <CodeBlock code={evt.code} language="python" />
                    </div>
                  );
                case 'tool.output': {
                  const tool: ToolViewModel = {
                    label: evt.tool_type,
                    state: 'output-available',
                    output: evt.output,
                  };
                  return (
                    <div className="mt-3">
                      <Tool defaultOpen={false}>
                        <ToolHeader type={`tool-${tool.label}` as const} state={tool.state} />
                        <ToolContent>
                          <ToolOutput output={renderToolOutput(tool)} errorText={undefined} />
                        </ToolContent>
                      </Tool>
                    </div>
                  );
                }
                case 'chunk.delta':
                  return (
                    <div className="mt-3">
                      <CodeBlock
                        code={JSON.stringify(
                          {
                            target: evt.target,
                            encoding: evt.encoding ?? null,
                            chunk_index: evt.chunk_index,
                            bytes: evt.data.length,
                          },
                          null,
                          2,
                        )}
                        language="json"
                      />
                    </div>
                  );
                case 'chunk.done':
                  return (
                    <div className="mt-3">
                      <CodeBlock
                        code={JSON.stringify({ target: evt.target }, null, 2)}
                        language="json"
                      />
                    </div>
                  );
                case 'error':
                  return (
                    <div className="mt-3">
                      <CodeBlock code={JSON.stringify(evt.error, null, 2)} language="json" />
                    </div>
                  );
                case 'final':
                  return (
                    <div className="mt-3">
                      <CodeBlock code={JSON.stringify(evt.final, null, 2)} language="json" />
                    </div>
                  );
                default:
                  return null;
              }
            })()}
          </div>
        );
      })}
    </div>
  );
}
