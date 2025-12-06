import { describe, expect, it } from 'vitest';

import type { ConversationListItem, ConversationSearchResultItem } from '@/types/conversations';
import { DATE_GROUP_ORDER, groupConversationsByDate, mapSearchResultsToListItems } from '../conversationGrouping';

describe('conversationGrouping', () => {
  it('groups conversations into date buckets in deterministic order', () => {
    const now = new Date('2025-12-05T12:00:00Z');
    const conversations: ConversationListItem[] = [
      { id: '1', updated_at: '2025-12-05T10:00:00Z' },
      { id: '2', updated_at: '2025-12-04T23:00:00Z' },
      { id: '3', updated_at: '2025-11-30T12:00:00Z' },
      { id: '4', updated_at: '2025-11-10T12:00:00Z' },
      { id: '5', updated_at: '2025-10-01T12:00:00Z' },
    ];

    const grouped = groupConversationsByDate(conversations, now);

    expect(Object.keys(grouped)).toEqual(expect.arrayContaining(DATE_GROUP_ORDER));
    expect(grouped['Today'].map((c) => c.id)).toEqual(['1']);
    expect(grouped['Yesterday'].map((c) => c.id)).toEqual(['2']);
    expect(grouped['Previous 7 Days'].map((c) => c.id)).toEqual(['3']);
    expect(grouped['Previous 30 Days'].map((c) => c.id)).toEqual(['4']);
    expect(grouped['Older'].map((c) => c.id)).toEqual(['5']);
  });

  it('maps search results to conversation list items', () => {
    const results: ConversationSearchResultItem[] = [
      {
        conversation_id: 'abc',
        preview: 'hello world',
        topic_hint: 'Greetings',
        active_agent: 'agent-1',
        agent_entrypoint: 'entrypoint-1',
        updated_at: '2025-12-01T00:00:00Z',
      },
    ];

    const mapped = mapSearchResultsToListItems(results);
    expect(mapped).toHaveLength(1);
    expect(mapped[0]).toMatchObject({
      id: 'abc',
      title: 'Greetings',
      last_message_preview: 'hello world',
      active_agent: 'agent-1',
    });
  });
});
