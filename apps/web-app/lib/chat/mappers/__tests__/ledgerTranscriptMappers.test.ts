import { describe, expect, it } from 'vitest';

import type { PublicSseEvent } from '@/lib/api/client/types.gen';

import type { ChatMessage } from '../../types';
import { enrichChatMessagesFromLedger } from '../ledgerTranscriptMappers';

describe('ledgerTranscriptMappers', () => {
  it('enriches assistant messages with citations and structured output from ledger final events', () => {
    const ledgerEvents: PublicSseEvent[] = [
      {
        schema: 'public_sse_v1',
        kind: 'message.delta',
        event_id: 1,
        stream_id: 'stream-1',
        server_timestamp: '2025-12-17T12:00:01.000Z',
        conversation_id: 'conv-1',
        response_id: 'resp-1',
        output_index: 0,
        item_id: 'item-msg',
        content_index: 0,
        delta: 'Hello world',
      },
      {
        schema: 'public_sse_v1',
        kind: 'message.citation',
        event_id: 2,
        stream_id: 'stream-1',
        server_timestamp: '2025-12-17T12:00:02.000Z',
        conversation_id: 'conv-1',
        response_id: 'resp-1',
        output_index: 0,
        item_id: 'item-msg',
        content_index: 0,
        citation: {
          type: 'url_citation',
          start_index: 0,
          end_index: 5,
          title: 'Example',
          url: 'https://example.com',
        },
      },
      {
        schema: 'public_sse_v1',
        kind: 'final',
        event_id: 3,
        stream_id: 'stream-1',
        server_timestamp: '2025-12-17T12:00:03.000Z',
        conversation_id: 'conv-1',
        response_id: 'resp-1',
        final: {
          status: 'completed',
          response_text: 'Hello world',
          structured_output: { ok: true },
          reasoning_summary_text: null,
          refusal_text: null,
          attachments: [],
          usage: null,
        },
      },
    ];

    const messages: ChatMessage[] = [
      {
        id: 'u1',
        role: 'user',
        content: 'Hi',
        timestamp: '2025-12-17T12:00:00.000Z',
      },
      {
        id: 'a1',
        role: 'assistant',
        content: '[persisted]',
        timestamp: '2025-12-17T12:00:05.000Z',
        citations: null,
        structuredOutput: null,
      },
    ];

    const enriched = enrichChatMessagesFromLedger(ledgerEvents, messages);

    expect(enriched).toHaveLength(2);
    expect(enriched[1]).toMatchObject({
      id: 'a1',
      role: 'assistant',
      content: 'Hello world',
      structuredOutput: { ok: true },
    });
    expect(enriched[1]?.citations?.[0]).toMatchObject({ type: 'url_citation', url: 'https://example.com' });
  });

  it('matches ledger final events to the correct assistant message when finals are emitted after persistence', () => {
    const ledgerEvents: PublicSseEvent[] = [
      {
        schema: 'public_sse_v1',
        kind: 'message.delta',
        event_id: 1,
        stream_id: 'stream-1',
        server_timestamp: '2025-12-17T12:00:01.000Z',
        conversation_id: 'conv-1',
        response_id: 'resp-1',
        output_index: 0,
        item_id: 'item-msg-1',
        content_index: 0,
        delta: 'First',
      },
      {
        schema: 'public_sse_v1',
        kind: 'final',
        event_id: 2,
        stream_id: 'stream-1',
        server_timestamp: '2025-12-17T12:00:02.000Z',
        conversation_id: 'conv-1',
        response_id: 'resp-1',
        final: {
          status: 'completed',
          response_text: 'First response',
          structured_output: null,
          reasoning_summary_text: null,
          refusal_text: null,
          attachments: [],
          usage: null,
        },
      },
      {
        schema: 'public_sse_v1',
        kind: 'message.delta',
        event_id: 3,
        stream_id: 'stream-2',
        server_timestamp: '2025-12-17T12:00:04.000Z',
        conversation_id: 'conv-1',
        response_id: 'resp-2',
        output_index: 0,
        item_id: 'item-msg-2',
        content_index: 0,
        delta: 'Second',
      },
      {
        schema: 'public_sse_v1',
        kind: 'final',
        event_id: 4,
        stream_id: 'stream-2',
        server_timestamp: '2025-12-17T12:00:05.000Z',
        conversation_id: 'conv-1',
        response_id: 'resp-2',
        final: {
          status: 'completed',
          response_text: 'Second response',
          structured_output: { ok: true },
          reasoning_summary_text: null,
          refusal_text: null,
          attachments: [],
          usage: null,
        },
      },
    ];

    const messages: ChatMessage[] = [
      {
        id: 'u1',
        role: 'user',
        content: 'hi',
        timestamp: '2025-12-17T12:00:00.000Z',
      },
      {
        id: 'a1',
        role: 'assistant',
        content: '[persisted-1]',
        timestamp: '2025-12-17T12:00:01.500Z',
        citations: null,
        structuredOutput: null,
      },
      {
        id: 'u2',
        role: 'user',
        content: 'what can you do',
        timestamp: '2025-12-17T12:00:03.000Z',
      },
      {
        id: 'a2',
        role: 'assistant',
        content: '[persisted-2]',
        timestamp: '2025-12-17T12:00:04.500Z',
        citations: null,
        structuredOutput: null,
      },
    ];

    const enriched = enrichChatMessagesFromLedger(ledgerEvents, messages);

    expect(enriched).toHaveLength(4);
    expect(enriched[1]?.content).toBe('First response');
    expect(enriched[3]?.content).toBe('Second response');
    expect(enriched[3]?.structuredOutput).toEqual({ ok: true });
  });
});
