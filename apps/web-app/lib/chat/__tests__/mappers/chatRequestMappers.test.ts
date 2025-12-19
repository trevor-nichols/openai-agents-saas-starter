import { describe, expect, it } from 'vitest';

import { dedupeAndSortMessages } from '../../mappers/chatRequestMappers';
import type { ChatMessage } from '../../types';

describe('dedupeAndSortMessages', () => {
  it('removes duplicates between ephemeral placeholders and persisted messages', () => {
    const messages: ChatMessage[] = [
      {
        id: 'user-1712345678901',
        role: 'user',
        content: 'Hello there',
        timestamp: '2025-01-01T00:00:00.000Z',
      },
      {
        id: 'msg_123',
        role: 'user',
        content: 'Hello there',
        timestamp: '2025-01-01T00:00:00.000Z',
      },
    ];

    const result = dedupeAndSortMessages(messages);

    expect(result).toHaveLength(1);
    expect(result[0]).toMatchObject({ role: 'user', content: 'Hello there' });
  });

  it('dedupes placeholders even when persisted timestamps differ slightly', () => {
    const messages: ChatMessage[] = [
      {
        id: 'assistant-1712345678901',
        role: 'assistant',
        content: 'Hi there▋',
        timestamp: '2025-01-01T00:00:00.000Z',
        isStreaming: true,
      },
      {
        id: 'msg_999',
        role: 'assistant',
        content: 'Hi there',
        timestamp: '2025-01-01T00:00:02.500Z',
      },
    ];

    const result = dedupeAndSortMessages(messages);

    expect(result).toHaveLength(1);
    expect(result[0]).toMatchObject({ role: 'assistant', content: 'Hi there' });
  });

  it('preserves citations when swapping placeholder for persisted message', () => {
    const messages: ChatMessage[] = [
      {
        id: 'assistant-1712345678901',
        role: 'assistant',
        content: 'Here is a link https://example.com',
        timestamp: '2025-01-01T00:00:00.000Z',
        citations: [
          {
            type: 'url_citation',
            start_index: 15,
            end_index: 34,
            title: 'Example',
            url: 'https://example.com',
          },
        ],
      },
      {
        id: 'msg_999',
        role: 'assistant',
        content: 'Here is a link https://example.com',
        timestamp: '2025-01-01T00:00:01.000Z',
        citations: null,
      },
    ];

    const result = dedupeAndSortMessages(messages);

    expect(result).toHaveLength(1);
    expect(result[0]?.id).toBe('msg_999');
    expect(result[0]?.citations).toHaveLength(1);
    expect(result[0]?.citations?.[0]).toMatchObject({ type: 'url_citation', url: 'https://example.com' });
  });

  it('dedupes multiple placeholders against multiple persisted messages', () => {
    const messages: ChatMessage[] = [
      {
        id: 'user-1712345678901',
        role: 'user',
        content: 'Repeat',
        timestamp: '2025-01-01T00:00:00.000Z',
      },
      {
        id: 'user-1712345679901',
        role: 'user',
        content: 'Repeat',
        timestamp: '2025-01-01T00:00:01.000Z',
      },
      {
        id: 'msg_1',
        role: 'user',
        content: 'Repeat',
        timestamp: '2025-01-01T00:00:03.000Z',
      },
      {
        id: 'msg_2',
        role: 'user',
        content: 'Repeat',
        timestamp: '2025-01-01T00:00:04.000Z',
      },
    ];

    const result = dedupeAndSortMessages(messages);

    expect(result).toHaveLength(2);
    expect(result.map((m) => m.id)).toEqual(['msg_1', 'msg_2']);
  });

  it('preserves distinct real messages with same content in the same second', () => {
    const messages: ChatMessage[] = [
      {
        id: 'msg_1',
        role: 'user',
        content: 'Repeat',
        timestamp: '2025-01-01T00:00:00.100Z',
      },
      {
        id: 'msg_2',
        role: 'user',
        content: 'Repeat',
        timestamp: '2025-01-01T00:00:00.900Z',
      },
    ];

    const result = dedupeAndSortMessages(messages);

    expect(result).toHaveLength(2);
    expect(result.map((m) => m.id)).toEqual(['msg_1', 'msg_2']);
  });
});
