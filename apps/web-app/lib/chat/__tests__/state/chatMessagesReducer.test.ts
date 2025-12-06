import { describe, expect, it } from 'vitest';

import { messagesReducer, type MessagesAction } from '../../state/messagesReducer';
import type { ChatMessage } from '../../types';

const baseAssistant: ChatMessage = {
  id: 'a1',
  role: 'assistant',
  content: 'hello',
};

const baseUser: ChatMessage = {
  id: 'u1',
  role: 'user',
  content: 'hi',
};

describe('messagesReducer', () => {
  it('appends and updates messages immutably', () => {
    const afterAppend = messagesReducer([], { type: 'append', message: baseUser });
    const afterUpdate = messagesReducer(afterAppend, {
      type: 'updateById',
      id: 'u1',
      patch: { content: 'hi there' },
    });

    expect(afterAppend).toHaveLength(1);
    expect(afterUpdate[0]!.content).toBe('hi there');
    expect(afterAppend[0]!.content).toBe('hi'); // immutability check
  });

  it('removes messages by id', () => {
    const state = [baseUser, baseAssistant];
    const afterRemove = messagesReducer(state, { type: 'removeById', id: 'u1' });
    expect(afterRemove).toEqual([baseAssistant]);
  });

  it('handles batch actions in sequence', () => {
    const actions: MessagesAction[] = [
      { type: 'append', message: baseUser },
      { type: 'append', message: baseAssistant },
      { type: 'updateById', id: 'a1', patch: { content: 'updated' } },
      { type: 'removeById', id: 'u1' },
    ];

    const result = messagesReducer([], { type: 'batch', actions });
    expect(result).toEqual([{ ...baseAssistant, content: 'updated' }]);
  });
});
