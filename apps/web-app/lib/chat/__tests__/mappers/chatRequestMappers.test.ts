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
