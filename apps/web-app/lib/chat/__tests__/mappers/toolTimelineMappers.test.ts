import { describe, expect, it } from 'vitest';

import {
  mapConversationEventsToToolTimeline,
  mergeToolEventAnchors,
  mergeToolStates,
  reanchorToolEventAnchors,
} from '../../mappers/toolTimelineMappers';
import type { ChatMessage, ToolEventAnchors, ToolState } from '../../types';
import type { ConversationEvent } from '@/types/conversations';

describe('mapConversationEventsToToolTimeline', () => {
  it('anchors a tool to the most recent loaded message before the tool started', () => {
    const messages: ChatMessage[] = [
      {
        id: '2025-01-01T00:00:00.000Z',
        role: 'user',
        content: 'Search for latest model',
        timestamp: '2025-01-01T00:00:00.000Z',
      },
      {
        id: '2025-01-01T00:00:10.000Z',
        role: 'assistant',
        content: 'Answer...',
        timestamp: '2025-01-01T00:00:10.000Z',
      },
    ];

    const events: ConversationEvent[] = [
      {
        sequence_no: 1,
        run_item_type: 'tool_call',
        tool_call_id: 'call-1',
        tool_name: 'web_search',
        call_arguments: { query: 'OpenAI latest model' },
        timestamp: '2025-01-01T00:00:05.000Z',
      },
      {
        sequence_no: 2,
        run_item_type: 'tool_result',
        tool_call_id: 'call-1',
        tool_name: 'web_search',
        call_output: { results: [{ title: 'Example' }] },
        timestamp: '2025-01-01T00:00:06.000Z',
      },
    ];

    const timeline = mapConversationEventsToToolTimeline(events, messages);

    expect(timeline.tools).toHaveLength(1);
    expect(timeline.tools[0]).toMatchObject({
      id: 'call-1',
      name: 'web_search',
      status: 'output-available',
      input: { query: 'OpenAI latest model' },
      output: { results: [{ title: 'Example' }] },
    });
    expect(timeline.anchors).toEqual({
      '2025-01-01T00:00:00.000Z': ['call-1'],
    });
  });

  it('skips tools that start before the oldest loaded message', () => {
    const messages: ChatMessage[] = [
      {
        id: '2025-01-01T00:00:10.000Z',
        role: 'assistant',
        content: 'Only the newest message is loaded',
        timestamp: '2025-01-01T00:00:10.000Z',
      },
    ];

    const events: ConversationEvent[] = [
      {
        sequence_no: 1,
        run_item_type: 'tool_call',
        tool_call_id: 'call-1',
        tool_name: 'web_search',
        call_arguments: { query: 'OpenAI latest model' },
        timestamp: '2025-01-01T00:00:05.000Z',
      },
    ];

    const timeline = mapConversationEventsToToolTimeline(events, messages);

    expect(timeline.tools).toEqual([]);
    expect(timeline.anchors).toEqual({});
  });

  it('preserves tool ordering within the same anchor', () => {
    const messages: ChatMessage[] = [
      {
        id: '2025-01-01T00:00:00.000Z',
        role: 'user',
        content: 'Do two searches',
        timestamp: '2025-01-01T00:00:00.000Z',
      },
    ];

    const events: ConversationEvent[] = [
      {
        sequence_no: 1,
        run_item_type: 'tool_call',
        tool_call_id: 'call-1',
        tool_name: 'web_search',
        call_arguments: { query: 'first' },
        timestamp: '2025-01-01T00:00:01.000Z',
      },
      {
        sequence_no: 2,
        run_item_type: 'tool_call',
        tool_call_id: 'call-2',
        tool_name: 'web_search',
        call_arguments: { query: 'second' },
        timestamp: '2025-01-01T00:00:02.000Z',
      },
    ];

    const timeline = mapConversationEventsToToolTimeline(events, messages);

    expect(timeline.anchors).toEqual({
      '2025-01-01T00:00:00.000Z': ['call-1', 'call-2'],
    });
    expect(timeline.tools.map((tool) => tool.id)).toEqual(['call-1', 'call-2']);
  });

  it('prefers event ordering over timestamps when anchoring tools', () => {
    const messages: ChatMessage[] = [
      {
        id: '2025-01-01T00:00:00.000Z',
        role: 'user',
        content: 'Search for something',
        timestamp: '2025-01-01T00:00:00.000Z',
      },
      {
        id: '2025-01-01T00:00:10.000Z',
        role: 'assistant',
        content: 'Final answer',
        timestamp: '2025-01-01T00:00:10.000Z',
      },
    ];

    const events: ConversationEvent[] = [
      {
        sequence_no: 1,
        run_item_type: 'user_message',
        role: 'user',
        content_text: 'Search for something',
        timestamp: '2025-01-01T00:00:00.000Z',
      },
      {
        sequence_no: 2,
        run_item_type: 'tool_call',
        tool_call_id: 'call-1',
        tool_name: 'web_search',
        call_arguments: { query: 'x' },
        // Intentionally after the assistant timestamp to ensure we don't anchor by time alone.
        timestamp: '2025-01-01T00:00:20.000Z',
      },
    ];

    const timeline = mapConversationEventsToToolTimeline(events, messages);

    expect(timeline.anchors).toEqual({
      '2025-01-01T00:00:00.000Z': ['call-1'],
    });
  });
});

describe('tool timeline merges', () => {
  it('mergeToolStates overlays tool state by id', () => {
    const base: ToolState[] = [
      { id: 'call-1', name: 'web_search', status: 'input-available', input: { q: 'x' } },
    ];
    const overlay: ToolState[] = [
      { id: 'call-1', name: 'web_search', status: 'output-available', output: { ok: true } },
      { id: 'call-2', name: 'file_search', status: 'output-available', output: [{ file_id: 'f1' }] },
    ];

    const merged = mergeToolStates(base, overlay);

    expect(merged).toHaveLength(2);
    expect(merged[0]).toMatchObject({
      id: 'call-1',
      status: 'output-available',
      input: { q: 'x' },
      output: { ok: true },
    });
    expect(merged[1]).toMatchObject({ id: 'call-2' });
  });

  it('mergeToolEventAnchors dedupes tool ids while preserving order', () => {
    const base: ToolEventAnchors = { msg_1: ['call-1', 'call-2'] };
    const overlay: ToolEventAnchors = { msg_1: ['call-2', 'call-3'], msg_2: ['call-9'] };

    expect(mergeToolEventAnchors(base, overlay)).toEqual({
      msg_1: ['call-1', 'call-2', 'call-3'],
      msg_2: ['call-9'],
    });
  });

  it('mergeToolEventAnchors prefers overlay anchors for duplicate tool ids', () => {
    const base: ToolEventAnchors = { msg_1: ['call-1', 'call-2'], msg_2: ['call-3'] };
    const overlay: ToolEventAnchors = { msg_9: ['call-2', 'call-4'] };

    expect(mergeToolEventAnchors(base, overlay)).toEqual({
      msg_1: ['call-1'],
      msg_2: ['call-3'],
      msg_9: ['call-2', 'call-4'],
    });
  });
});

describe('reanchorToolEventAnchors', () => {
  it('reanchors placeholder message ids to persisted messages with the same signature', () => {
    const sourceMessages: ChatMessage[] = [
      {
        id: 'user-1712345678901',
        role: 'user',
        content: 'Search for latest model',
        timestamp: '2025-01-01T00:00:00.000Z',
      },
    ];
    const targetMessages: ChatMessage[] = [
      {
        id: '2025-01-01T00:00:01.000Z',
        role: 'user',
        content: 'Search for latest model',
        timestamp: '2025-01-01T00:00:01.000Z',
      },
    ];
    const anchors: ToolEventAnchors = {
      'user-1712345678901': ['call-1'],
    };

    expect(reanchorToolEventAnchors(anchors, sourceMessages, targetMessages)).toEqual({
      '2025-01-01T00:00:01.000Z': ['call-1'],
    });
  });

  it('reanchors even when the persisted timestamp includes microseconds or lacks timezone', () => {
    const sourceMessages: ChatMessage[] = [
      {
        id: 'user-1712345678901',
        role: 'user',
        content: 'Search for latest model',
        timestamp: '2025-01-01T00:00:00.000Z',
      },
    ];
    const targetMessages: ChatMessage[] = [
      {
        id: '2025-01-01T00:00:01.123456',
        role: 'user',
        content: 'Search for latest model',
        timestamp: '2025-01-01T00:00:01.123456',
      },
    ];
    const anchors: ToolEventAnchors = {
      'user-1712345678901': ['call-1'],
    };

    expect(reanchorToolEventAnchors(anchors, sourceMessages, targetMessages)).toEqual({
      '2025-01-01T00:00:01.123456': ['call-1'],
    });
  });

  it('keeps existing anchors when the anchor id still exists in the target message list', () => {
    const sourceMessages: ChatMessage[] = [
      {
        id: 'msg_1',
        role: 'user',
        content: 'Hello',
        timestamp: '2025-01-01T00:00:00.000Z',
      },
    ];
    const targetMessages: ChatMessage[] = [...sourceMessages];
    const anchors: ToolEventAnchors = { msg_1: ['call-1', 'call-2'] };

    expect(reanchorToolEventAnchors(anchors, sourceMessages, targetMessages)).toEqual({
      msg_1: ['call-1', 'call-2'],
    });
  });

  it('drops anchors that cannot be remapped to any visible message', () => {
    const sourceMessages: ChatMessage[] = [
      {
        id: 'user-1712345678901',
        role: 'user',
        content: 'Unique prompt',
        timestamp: '2025-01-01T00:00:00.000Z',
      },
    ];
    const targetMessages: ChatMessage[] = [
      {
        id: '2025-01-01T00:00:30.000Z',
        role: 'user',
        content: 'Different prompt',
        timestamp: '2025-01-01T00:00:30.000Z',
      },
    ];
    const anchors: ToolEventAnchors = {
      'user-1712345678901': ['call-1'],
    };

    expect(reanchorToolEventAnchors(anchors, sourceMessages, targetMessages)).toEqual({});
  });
});
