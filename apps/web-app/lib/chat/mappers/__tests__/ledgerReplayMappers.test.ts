import { describe, expect, it } from 'vitest';

import type { PublicSseEvent } from '@/lib/api/client/types.gen';

import { extractMemoryCheckpointMarkers, mapLedgerEventsToToolTimeline } from '../ledgerReplayMappers';

describe('ledgerReplayMappers', () => {
  it('extractMemoryCheckpointMarkers returns stable marker messages', () => {
    const events: PublicSseEvent[] = [
      {
        schema: 'public_sse_v1',
        kind: 'memory.checkpoint',
        event_id: 3,
        stream_id: 'stream-1',
        server_timestamp: '2025-12-17T12:00:06.000Z',
        conversation_id: 'conv-1',
        checkpoint: {
          strategy: 'compact',
        },
      },
    ];

    const markers = extractMemoryCheckpointMarkers(events);
    expect(markers).toHaveLength(1);
    expect(markers[0]).toMatchObject({
      id: 'memory-checkpoint-stream-1-3',
      role: 'assistant',
      kind: 'memory_checkpoint',
    });
    expect(markers[0]?.checkpoint?.strategy).toBe('compact');
  });

  it('mapLedgerEventsToToolTimeline anchors tools to the nearest prior message', () => {
    const events: PublicSseEvent[] = [
      {
        schema: 'public_sse_v1',
        kind: 'tool.status',
        event_id: 2,
        stream_id: 'stream-1',
        server_timestamp: '2025-12-17T12:00:05.000Z',
        conversation_id: 'conv-1',
        output_index: 0,
        item_id: 'item-1',
        tool: {
          tool_type: 'function',
          tool_call_id: 'call_1',
          status: 'completed',
          name: 'my_tool',
          arguments_text: '{}',
          arguments_json: {},
          output: { ok: true },
        },
      },
    ];

    const messages = [
      {
        id: 'u1',
        role: 'user' as const,
        content: 'Hi',
        timestamp: '2025-12-17T12:00:00.000Z',
      },
      {
        id: 'a1',
        role: 'assistant' as const,
        content: 'Hello',
        timestamp: '2025-12-17T12:00:10.000Z',
      },
    ];

    const timeline = mapLedgerEventsToToolTimeline(events, messages);
    expect(timeline.tools).toHaveLength(1);
    expect(timeline.tools[0]).toMatchObject({
      id: 'call_1',
      name: 'my_tool',
      status: 'output-available',
    });
    expect(timeline.anchors).toEqual({ u1: ['call_1'] });
  });
});

