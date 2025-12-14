import { readFileSync } from 'node:fs';
import path from 'node:path';

import { describe, expect, it, vi } from 'vitest';

import { consumeChatStream } from '../../adapters/chatStreamAdapter';
import type { StreamChunk, ToolState, UrlCitation } from '../../types';

async function* chunkStream(chunks: StreamChunk[]) {
  for (const chunk of chunks) {
    yield chunk;
  }
}

describe('consumeChatStream', () => {
  it('accumulates deltas, updates lifecycle, and emits final content', async () => {
    const onTextDelta = vi.fn();
    const onLifecycle = vi.fn();

    const chunks: StreamChunk[] = [
      {
        type: 'event',
        event: {
          conversation_id: 'c1',
          kind: 'raw_response_event',
          raw_type: 'response.output_text.delta',
          text_delta: 'Hello',
        },
      },
      {
        type: 'event',
        event: {
          conversation_id: 'c1',
          kind: 'raw_response_event',
          raw_type: 'response.output_text.delta',
          text_delta: ' world',
        },
      },
      {
        type: 'event',
        event: {
          conversation_id: 'c1',
          kind: 'raw_response_event',
          raw_type: 'response.completed',
          response_text: 'Override text',
          is_terminal: true,
        },
      },
    ];

    const result = await consumeChatStream(chunkStream(chunks), {
      onTextDelta,
      onLifecycle,
    });

    expect(onTextDelta).toHaveBeenCalledTimes(2);
    expect(onLifecycle).toHaveBeenCalledWith('completed');
    expect(result.finalContent).toBe('Override text');
    expect(result.lifecycleStatus).toBe('completed');
    expect(result.errored).toBe(false);
  });

  it('collects tool events and agent notices', async () => {
    const toolStates: ToolState[][] = [];
    const notices: string[] = [];
    const agentChanges: string[] = [];

    const chunks: StreamChunk[] = [
      {
        type: 'event',
        event: {
          conversation_id: 'c2',
          kind: 'agent_updated_stream_event',
          new_agent: 'assistant-2',
        },
      },
      {
        type: 'event',
        event: {
          conversation_id: 'c2',
          kind: 'run_item_stream_event',
          run_item_name: 'tool_called',
          tool_call_id: 'tool-1',
          tool_name: 'search',
          payload: { q: 'hello' },
        },
      },
      {
        type: 'event',
        event: {
          conversation_id: 'c2',
          kind: 'run_item_stream_event',
          run_item_name: 'tool_output',
          tool_call_id: 'tool-1',
          tool_name: 'search',
          payload: { results: [] },
          is_terminal: true,
        },
      },
    ];

    const result = await consumeChatStream(chunkStream(chunks), {
      onToolStates: (tools) => toolStates.push(tools),
      onAgentNotice: (notice) => notices.push(notice),
      onAgentChange: (agent) => agentChanges.push(agent),
    });

    expect(agentChanges).toEqual(['assistant-2']);
    expect(notices[0]).toContain('Switched to assistant-2');
    expect(toolStates.at(-1)?.[0]?.status).toBe('output-available');
    expect(result.errored).toBe(false);
  });

  it('does not downgrade tool status when run item events arrive after a completed raw tool call', async () => {
    const toolStates: ToolState[][] = [];

    const chunks: StreamChunk[] = [
      {
        type: 'event',
        event: {
          conversation_id: 'c3',
          kind: 'raw_response_event',
          raw_type: 'response.web_search_call.completed',
          tool_call: {
            tool_type: 'web_search',
            web_search_call: { id: 'call-1', type: 'web_search_call', status: 'completed', action: null },
          },
        },
      },
      {
        type: 'event',
        event: {
          conversation_id: 'c3',
          kind: 'run_item_stream_event',
          run_item_name: 'tool_called',
          run_item_type: 'tool_call_item',
          tool_call_id: 'call-1',
          payload: {
            raw_item: {
              type: 'web_search_call',
              action: { type: 'search', query: 'latest OpenAI model' },
              status: 'completed',
            },
          },
        },
      },
      {
        type: 'event',
        event: {
          conversation_id: 'c3',
          kind: 'raw_response_event',
          raw_type: 'response.completed',
          is_terminal: true,
        },
      },
    ];

    const result = await consumeChatStream(chunkStream(chunks), {
      onToolStates: (tools) => toolStates.push(tools),
    });

    expect(result.errored).toBe(false);
    expect(toolStates.length).toBeGreaterThan(0);
    expect(toolStates.at(-1)?.[0]).toMatchObject({
      id: 'call-1',
      name: 'web_search',
      status: 'output-available',
      input: 'latest OpenAI model',
    });
  });

  it('marks errored streams', async () => {
    const chunks: StreamChunk[] = [
      { type: 'error', payload: 'boom' },
    ];

    const result = await consumeChatStream(chunkStream(chunks), {});
    expect(result.errored).toBe(true);
  });

  it('ignores null structured_output payloads', async () => {
    const onStructuredOutput = vi.fn();

    const chunks: StreamChunk[] = [
      {
        type: 'event',
        event: {
          conversation_id: 'so-null',
          kind: 'agent_updated_stream_event',
          new_agent: 'Researcher',
          structured_output: null,
        },
      },
      {
        type: 'event',
        event: {
          conversation_id: 'so-null',
          kind: 'raw_response_event',
          raw_type: 'response.completed',
          structured_output: null,
          is_terminal: true,
        },
      },
    ];

    const result = await consumeChatStream(chunkStream(chunks), { onStructuredOutput });
    expect(onStructuredOutput).not.toHaveBeenCalled();
    expect(result.structuredOutput).toBe(null);
  });

  it('emits guardrail events to handler and accumulates', async () => {
    const guardrailEvents: string[] = [];

    const chunks: StreamChunk[] = [
      {
        type: 'event',
        event: {
          conversation_id: 'g1',
          kind: 'guardrail_result',
          guardrail_key: 'pii_mask',
          guardrail_name: 'PII Masking',
          guardrail_stage: 'input',
        },
      },
      {
        type: 'event',
        event: {
          conversation_id: 'g1',
          kind: 'guardrail_result',
          guardrail_key: 'safety',
          guardrail_name: 'Safety',
          guardrail_stage: 'output',
          is_terminal: true,
        },
      },
    ];

    const result = await consumeChatStream(chunkStream(chunks), {
      onGuardrailEvents: (events) => {
        guardrailEvents.push(events.map((e) => e.guardrail_key).join(','));
      },
    });

    expect(guardrailEvents).toEqual(['pii_mask', 'pii_mask,safety']);
    expect(result.errored).toBe(false);
  });

  it('parses web_search tool calls and citations from SDK fixture', async () => {
    const fixturePath = path.resolve(
      __dirname,
      '../../../../../../docs/integrations/openai-agents-sdk/runner_api_events/tool_events.json',
    );
    const log = JSON.parse(readFileSync(fixturePath, 'utf-8')) as {
      raw_events: Array<Record<string, unknown>>;
    };
    const annotationEvent = log.raw_events.find((ev) => ev.type === 'response.output_text.annotation.added');
    const webSearchCompleted = log.raw_events.find((ev) => ev.type === 'response.web_search_call.completed');

    expect(annotationEvent).toBeTruthy();
    expect(webSearchCompleted).toBeTruthy();

    const chunks: StreamChunk[] = [
      {
        type: 'event',
        event: {
          kind: 'raw_response_event',
          conversation_id: 'fixture',
          raw_type: annotationEvent?.type as string,
          payload: annotationEvent,
          raw_event: annotationEvent,
          annotations: annotationEvent && 'annotation' in annotationEvent ? [annotationEvent.annotation as UrlCitation] : undefined,
        },
      },
      {
        type: 'event',
        event: {
          kind: 'raw_response_event',
          conversation_id: 'fixture',
          raw_type: webSearchCompleted?.type as string,
          payload: webSearchCompleted,
          raw_event: webSearchCompleted,
          tool_call: {
            tool_type: 'web_search',
            web_search_call: {
              id: String((webSearchCompleted as { item_id?: unknown })?.item_id ?? ''),
              type: 'web_search_call',
              status: 'completed',
              action: null,
            },
          },
        },
      },
      {
        type: 'event',
        event: {
          kind: 'raw_response_event',
          conversation_id: 'fixture',
          raw_type: 'response.completed',
          is_terminal: true,
        },
      },
    ];

    const toolStates: ToolState[][] = [];
    const result = await consumeChatStream(chunkStream(chunks), {
      onToolStates: (tools) => toolStates.push(tools),
    });

    const lastTool = toolStates.at(-1)?.[0];
    expect(lastTool?.name).toBe('web_search');
    expect(lastTool?.status).toBe('output-available');
    expect(result.citations?.length).toBeGreaterThanOrEqual(1);
    expect(result.errored).toBe(false);
  });

  it('does not duplicate citations when both payload.annotation and annotations are present', async () => {
    const annotation = {
      type: 'url_citation',
      start_index: 0,
      end_index: 4,
      title: 'Example',
      url: 'https://example.com',
    } satisfies UrlCitation;

    const chunks: StreamChunk[] = [
      {
        type: 'event',
        event: {
          kind: 'raw_response_event',
          conversation_id: 'dup',
          raw_type: 'response.output_text.annotation.added',
          payload: { annotation },
          annotations: [annotation],
        },
      },
      {
        type: 'event',
        event: {
          kind: 'raw_response_event',
          conversation_id: 'dup',
          raw_type: 'response.completed',
          is_terminal: true,
        },
      },
    ];

    const result = await consumeChatStream(chunkStream(chunks), {});
    expect(result.citations).toEqual([annotation]);
  });

  it('parses code_interpreter tool calls and code deltas', async () => {
    const chunks: StreamChunk[] = [
      {
        type: 'event',
        event: {
          kind: 'raw_response_event',
          conversation_id: 'ci',
          raw_type: 'response.code_interpreter_call.in_progress',
          payload: { item_id: 'ci_1' },
          tool_call: {
            tool_type: 'code_interpreter',
            code_interpreter_call: {
              id: 'ci_1',
              type: 'code_interpreter_call',
              status: 'in_progress',
              code: null,
              outputs: null,
            },
          },
        },
      },
      {
        type: 'event',
        event: {
          kind: 'raw_response_event',
          conversation_id: 'ci',
          raw_type: 'response.code_interpreter_call_code.delta',
          payload: { item_id: 'ci_1', delta: 'print(1)' },
          tool_call: {
            tool_type: 'code_interpreter',
            code_interpreter_call: {
              id: 'ci_1',
              type: 'code_interpreter_call',
              status: 'in_progress',
              code: 'print(1)',
              outputs: null,
            },
          },
        },
      },
      {
        type: 'event',
        event: {
          kind: 'run_item_stream_event',
          conversation_id: 'ci',
          run_item_name: 'tool_output',
          run_item_type: 'tool_call_output_item',
          tool_call_id: 'ci_1',
          payload: { outputs: [{ text: '1' }] },
          tool_call: {
            tool_type: 'code_interpreter',
            code_interpreter_call: {
              id: 'ci_1',
              type: 'code_interpreter_call',
              status: 'completed',
              code: 'print(1)',
              outputs: [{ text: '1' }],
            },
          },
        },
      },
      {
        type: 'event',
        event: {
          kind: 'raw_response_event',
          conversation_id: 'ci',
          raw_type: 'response.completed',
          is_terminal: true,
        },
      },
    ];

    const toolStates: ToolState[][] = [];
    const result = await consumeChatStream(chunkStream(chunks), {
      onToolStates: (tools) => toolStates.push(tools),
    });

    const lastTool = toolStates.at(-1)?.[0];
    expect(lastTool?.name).toBe('code_interpreter');
    expect(lastTool?.status).toBe('output-available');
    expect(lastTool?.output).toEqual([{ text: '1' }]);
    expect(result.errored).toBe(false);
  });

  it('parses file_search tool calls', async () => {
    const chunks: StreamChunk[] = [
      {
        type: 'event',
        event: {
          kind: 'raw_response_event',
          conversation_id: 'fs',
          raw_type: 'response.file_search_call.in_progress',
          payload: { item_id: 'fs_1' },
          tool_call: undefined,
        },
      },
      {
        type: 'event',
        event: {
          kind: 'run_item_stream_event',
          conversation_id: 'fs',
          run_item_name: 'tool_output',
          run_item_type: 'tool_call_output_item',
          tool_call_id: 'fs_1',
          payload: { results: [{ id: 'doc1' }] },
          tool_call: {
            tool_type: 'file_search',
            file_search_call: {
              id: 'fs_1',
              type: 'file_search_call',
              status: 'completed',
              queries: ['what is deep research'],
              results: [{ id: 'doc1' }],
            },
          },
        },
      },
      {
        type: 'event',
        event: {
          kind: 'raw_response_event',
          conversation_id: 'fs',
          raw_type: 'response.completed',
          is_terminal: true,
        },
      },
    ];

    const toolStates: ToolState[][] = [];
    const result = await consumeChatStream(chunkStream(chunks), {
      onToolStates: (tools) => toolStates.push(tools),
    });

    const lastToolStateList = toolStates.at(-1);
    const fileSearch = lastToolStateList?.find((t) => t.name === 'file_search');
    expect(fileSearch?.status).toBe('output-available');
    expect(fileSearch?.output).toEqual([{ id: 'doc1' }]);
    expect(result.errored).toBe(false);
  });
});
