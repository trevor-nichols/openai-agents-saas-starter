import { describe, expect, it } from 'vitest';

import type { PublicSseEvent } from '@/lib/api/client/types.gen';
import { createAgentToolStreamAccumulator } from '@/lib/streams/publicSseV1/agentToolStreams';

const scoped = (kind: PublicSseEvent['kind']) =>
  ({
    schema: 'public_sse_v1',
    event_id: 1,
    stream_id: 'stream-test',
    server_timestamp: '2025-12-17T00:00:00.000Z',
    kind,
    output_index: 0,
    item_id: 'msg_1',
    scope: {
      type: 'agent_tool',
      tool_call_id: 'call_agent_1',
      tool_name: 'ask_researcher',
      agent: 'researcher',
    },
  }) as unknown as PublicSseEvent;

describe('agent tool stream accumulator', () => {
  it('ignores unscoped events', () => {
    const acc = createAgentToolStreamAccumulator();
    acc.apply({
      ...scoped('message.delta'),
      scope: null,
      delta: 'hello',
      content_index: 0,
    } as unknown as PublicSseEvent);
    expect(acc.getStreams()).toHaveLength(0);
  });

  it('accumulates scoped message text for a tool call', () => {
    const acc = createAgentToolStreamAccumulator();

    acc.apply({
      ...scoped('output_item.added'),
      item_type: 'message',
      role: 'assistant',
      status: 'in_progress',
    } as unknown as PublicSseEvent);

    acc.apply({
      ...scoped('message.delta'),
      delta: 'Top-line TAM estimate',
      content_index: 0,
    } as unknown as PublicSseEvent);

    acc.apply({
      ...scoped('output_item.done'),
      item_type: 'message',
      role: 'assistant',
      status: 'completed',
    } as unknown as PublicSseEvent);

    const stream = acc.getStream('call_agent_1');
    expect(stream).toBeTruthy();
    expect(stream?.toolCallId).toBe('call_agent_1');
    expect(stream?.agent).toBe('researcher');
    expect(stream?.toolName).toBe('ask_researcher');
    expect(stream?.text).toContain('Top-line TAM estimate');
    expect(stream?.isStreaming).toBe(false);
  });
});
