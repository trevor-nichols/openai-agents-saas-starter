import { describe, expect, it } from 'vitest';

import type { StreamingWorkflowEvent } from '@/lib/api/client/types.gen';
import { buildWorkflowLiveTranscript } from '../liveStreamTranscript';

const base = {
  schema: 'public_sse_v1',
  stream_id: 'stream_1',
  server_timestamp: '2025-12-16T00:00:00.000Z',
  conversation_id: 'conv_1',
} as const;

function e<T extends StreamingWorkflowEvent>(event: T): StreamingWorkflowEvent {
  return event as StreamingWorkflowEvent;
}

describe('buildWorkflowLiveTranscript', () => {
  it('renders rows ordered by output_index (not arrival order)', () => {
    const events: StreamingWorkflowEvent[] = [
      e({
        ...base,
        event_id: 1,
        kind: 'message.delta',
        response_id: 'resp_1',
        agent: 'agent_a',
        workflow: null,
        provider_sequence_number: 2,
        notices: null,
        output_index: 1,
        item_id: 'msg_1',
        content_index: 0,
        delta: 'Hello',
      }),
      e({
        ...base,
        event_id: 2,
        kind: 'tool.status',
        response_id: 'resp_1',
        agent: 'agent_a',
        workflow: null,
        provider_sequence_number: 1,
        notices: null,
        output_index: 0,
        item_id: 'tool_1',
        tool: {
          tool_type: 'web_search',
          tool_call_id: 'tool_1',
          status: 'completed',
          query: 'q',
          sources: ['https://example.com'],
        },
      }),
      e({
        ...base,
        event_id: 3,
        kind: 'output_item.done',
        response_id: 'resp_1',
        agent: 'agent_a',
        workflow: null,
        provider_sequence_number: 3,
        notices: null,
        output_index: 1,
        item_id: 'msg_1',
        item_type: 'message',
        role: 'assistant',
        status: 'completed',
      }),
    ];

    const segments = buildWorkflowLiveTranscript(events);
    expect(segments).toHaveLength(1);
    expect(segments[0]?.items.map((i) => i.outputIndex)).toEqual([0, 1]);
    expect(segments[0]?.items[0]?.kind).toBe('tool');
    expect(segments[0]?.items[1]?.kind).toBe('message');
  });

  it('keeps separate response segments when output_index resets', () => {
    const events: StreamingWorkflowEvent[] = [
      e({
        ...base,
        event_id: 1,
        kind: 'message.delta',
        response_id: 'resp_1',
        agent: 'agent_a',
        workflow: null,
        provider_sequence_number: 1,
        notices: null,
        output_index: 0,
        item_id: 'msg_1',
        content_index: 0,
        delta: 'Step 1',
      }),
      e({
        ...base,
        event_id: 2,
        kind: 'message.delta',
        response_id: 'resp_2',
        agent: 'agent_b',
        workflow: null,
        provider_sequence_number: 1,
        notices: null,
        output_index: 0,
        item_id: 'msg_2',
        content_index: 0,
        delta: 'Step 2',
      }),
    ];

    const segments = buildWorkflowLiveTranscript(events);
    expect(segments.map((s) => s.responseId)).toEqual(['resp_1', 'resp_2']);
    expect(segments[0]?.items[0]).toMatchObject({ kind: 'message', itemId: 'msg_1', outputIndex: 0 });
    expect(segments[1]?.items[0]).toMatchObject({ kind: 'message', itemId: 'msg_2', outputIndex: 0 });
  });
});

