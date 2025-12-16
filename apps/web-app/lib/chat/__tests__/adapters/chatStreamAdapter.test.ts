import { readFileSync } from 'node:fs';
import path from 'node:path';

import { describe, expect, it, vi } from 'vitest';

import { consumeChatStream } from '../../adapters/chatStreamAdapter';
import type { StreamChunk, ToolState } from '../../types';
import type { StreamingChatEvent } from '@/lib/api/client/types.gen';
import type { GeneratedImageFrame } from '@/lib/streams/imageFrames';

async function* chunkStream(chunks: StreamChunk[]) {
  for (const chunk of chunks) {
    yield chunk;
  }
}

function loadContractExample(filename: string): StreamingChatEvent[] {
  const fixturePath = path.resolve(
    __dirname,
    `../../../../../../docs/contracts/public-sse-streaming/examples/${filename}`,
  );
  const raw = readFileSync(fixturePath, 'utf-8');
  return raw
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line) => JSON.parse(line) as StreamingChatEvent);
}

describe('consumeChatStream (public_sse_v1)', () => {
  it('accumulates message deltas and uses final response_text', async () => {
    const onTextDelta = vi.fn();

    const events: StreamingChatEvent[] = [
      {
        schema: 'public_sse_v1',
        event_id: 1,
        stream_id: 'stream_test',
        server_timestamp: '2025-12-15T00:00:00.000Z',
        kind: 'message.delta',
        conversation_id: 'c1',
        response_id: 'resp_1',
        agent: 'triage',
        message_id: 'msg_1',
        delta: 'Hello',
      },
      {
        schema: 'public_sse_v1',
        event_id: 2,
        stream_id: 'stream_test',
        server_timestamp: '2025-12-15T00:00:00.050Z',
        kind: 'message.delta',
        conversation_id: 'c1',
        response_id: 'resp_1',
        agent: 'triage',
        message_id: 'msg_1',
        delta: ' world',
      },
      {
        schema: 'public_sse_v1',
        event_id: 3,
        stream_id: 'stream_test',
        server_timestamp: '2025-12-15T00:00:00.100Z',
        kind: 'final',
        conversation_id: 'c1',
        response_id: 'resp_1',
        agent: 'triage',
        final: {
          status: 'completed',
          response_text: 'Override text',
          structured_output: null,
          reasoning_summary_text: null,
          refusal_text: null,
          attachments: [],
          usage: { input_tokens: 1, output_tokens: 2, total_tokens: 3 },
        },
      },
    ];

    const chunks: StreamChunk[] = events.map((event) => ({ type: 'event', event }));

    const result = await consumeChatStream(chunkStream(chunks), { onTextDelta });

    expect(onTextDelta).toHaveBeenCalled();
    expect(result.finalContent).toBe('Override text');
    expect(result.lifecycleStatus).toBe('completed');
    expect(result.terminalSeen).toBe(true);
    expect(result.errored).toBe(false);
  });

  it('captures function tool arguments and outputs (contract example)', async () => {
    const toolStates: ToolState[][] = [];
    const events = loadContractExample('chat-function-tool.ndjson');
    const chunks: StreamChunk[] = events.map((event) => ({ type: 'event', event }));

    const result = await consumeChatStream(chunkStream(chunks), {
      onToolStates: (tools) => toolStates.push(tools),
    });

    const last = toolStates.at(-1) ?? [];
    expect(last.length).toBeGreaterThan(0);
    expect(last[0]).toMatchObject({
      id: 'call_001',
      name: 'get_current_time',
      status: 'output-available',
    });

    expect(last[0]?.input).toMatchObject({
      tool_type: 'function',
      tool_name: 'get_current_time',
      arguments_json: { timezone: 'UTC' },
    });
    expect(last[0]?.output).toMatchObject({
      timezone: 'UTC',
      iso: '2025-12-15T12:10:00Z',
    });

    expect(result.finalContent).toContain('Current time');
    expect(result.lifecycleStatus).toBe('completed');
    expect(result.errored).toBe(false);
  });

  it('streams reasoning summary deltas (contract example)', async () => {
    const onReasoningDelta = vi.fn();
    const events = loadContractExample('chat-reasoning-summary.ndjson');
    const chunks: StreamChunk[] = events.map((event) => ({ type: 'event', event }));

    const result = await consumeChatStream(chunkStream(chunks), { onReasoningDelta });

    expect(onReasoningDelta).toHaveBeenCalledTimes(2);
    expect(result.finalContent).toContain('Here’s a concise answer');
    expect(result.lifecycleStatus).toBe('completed');
    expect(result.errored).toBe(false);
  });

  it('treats refusals as first-class terminal state (contract example)', async () => {
    const onTextDelta = vi.fn();
    const events = loadContractExample('chat-refusal.ndjson');
    const chunks: StreamChunk[] = events.map((event) => ({ type: 'event', event }));

    const result = await consumeChatStream(chunkStream(chunks), { onTextDelta });

    expect(onTextDelta).toHaveBeenCalled();
    expect(result.lifecycleStatus).toBe('refused');
    expect(result.finalContent).toContain('I can’t help with that request');
    expect(result.terminalSeen).toBe(true);
    expect(result.errored).toBe(false);
  });

  it('builds image frames from chunk events (contract example)', async () => {
    const toolStates: ToolState[][] = [];
    const events = loadContractExample('chat-image-generation-partials.ndjson');
    const chunks: StreamChunk[] = events.map((event) => ({ type: 'event', event }));

    const result = await consumeChatStream(chunkStream(chunks), {
      onToolStates: (tools) => toolStates.push(tools),
    });

    const flattened = toolStates.flat();
    const imageTool = [...flattened].reverse().find((tool) => tool.id === 'img_123');

    expect(imageTool).toBeTruthy();
    expect(imageTool?.output).toBeTruthy();

    const frames = imageTool?.output as GeneratedImageFrame[] | undefined;
    expect(Array.isArray(frames)).toBe(true);
    expect(frames?.[0]?.src).toContain('data:image/');

    expect(result.lifecycleStatus).toBe('completed');
    expect(result.attachments?.[0]).toMatchObject({
      object_id: 'obj_img_001',
      filename: 'image.png',
      mime_type: 'image/png',
    });
  });

  it('surfaces terminal provider/server errors (contract example)', async () => {
    const onError = vi.fn();
    const events = loadContractExample('chat-provider-error.ndjson');
    const chunks: StreamChunk[] = events.map((event) => ({ type: 'event', event }));

    const result = await consumeChatStream(chunkStream(chunks), { onError });

    expect(onError).toHaveBeenCalledWith('The request was invalid.');
    expect(result.errored).toBe(true);
    expect(result.terminalSeen).toBe(true);
  });
});
