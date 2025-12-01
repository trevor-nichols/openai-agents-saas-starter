import { describe, expect, it, vi } from 'vitest';

import { consumeChatStream } from '../../adapters/chatStreamAdapter';
import type { StreamChunk, ToolState } from '../../types';

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

  it('marks errored streams', async () => {
    const chunks: StreamChunk[] = [
      { type: 'error', payload: 'boom' },
    ];

    const result = await consumeChatStream(chunkStream(chunks), {});
    expect(result.errored).toBe(true);
  });
});
