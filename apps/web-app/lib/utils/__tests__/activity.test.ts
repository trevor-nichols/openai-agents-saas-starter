import { describe, expect, it } from 'vitest';

import { mergeActivityEvents, humanizeAction, summarizeMetadata, toActivityDisplayItem } from '../activity';
import type { ActivityEvent } from '@/types/activity';

const baseEvent: ActivityEvent = {
  id: 'evt-1',
  tenant_id: 'tenant-1',
  action: 'agent.run',
  created_at: '2024-01-01T00:00:00Z',
  status: 'success',
};

describe('activity utils', () => {
  it('humanizes dotted actions', () => {
    expect(humanizeAction('foo.bar')).toBe('Foo Bar');
    expect(humanizeAction(null)).toBe('Activity');
  });

  it('summarizes metadata with up to two entries', () => {
    expect(summarizeMetadata({ one: '1', two: 2, three: 3 })).toBe('one: 1 • two: 2');
    expect(summarizeMetadata(undefined)).toBeNull();
  });

  it('dedupes and truncates merged activity', () => {
    const live = [{ ...baseEvent, id: 'live-1' }];
    const cached = [
      { ...baseEvent, id: 'live-1', action: 'duplicate' },
      { ...baseEvent, id: 'cached-1' },
    ];

    const result = mergeActivityEvents(live, cached, 2);
    expect(result.map((e) => e.id)).toEqual(['live-1', 'cached-1']);
  });

  it('filters dismissed events client-side by default but keeps others', () => {
    const live = [
      { ...baseEvent, id: 'live-keep' },
      { ...baseEvent, id: 'live-dismiss', read_state: 'dismissed' as const },
    ];
    const cached = [{ ...baseEvent, id: 'cached-keep' }];

    const result = mergeActivityEvents(live, cached, 5);
    expect(result.map((e) => e.id)).toEqual(['live-keep', 'cached-keep']);
  });

  it('can include dismissed events when requested', () => {
    const live = [
      { ...baseEvent, id: 'live-keep' },
      { ...baseEvent, id: 'live-dismiss', read_state: 'dismissed' as const },
    ];
    const cached = [{ ...baseEvent, id: 'cached-keep' }];

    const result = mergeActivityEvents(live, cached, 5, { includeDismissed: true });
    expect(result.map((e) => e.id)).toEqual(['live-keep', 'live-dismiss', 'cached-keep']);
  });

  it('uses cached state to override live unread copies', () => {
    const live = [
      { ...baseEvent, id: 'evt-1', read_state: 'unread' as const },
    ];
    const cached = [
      { ...baseEvent, id: 'evt-1', read_state: 'read' as const },
    ];

    const result = mergeActivityEvents(live, cached, 5);
    expect(result).toHaveLength(1);
    const [first] = result;
    expect(first?.read_state).toBe('read');
  });

  it('projects an activity event into display item', () => {
    const item = toActivityDisplayItem({
      ...baseEvent,
      object_type: 'conversation',
      object_id: 'abc',
      metadata: { trace: 'xyz' },
    });

    expect(item.title).toBe('Agent Run');
    expect(item.detail).toBe('conversation • abc');
    expect(item.metadataSummary).toBe('trace: xyz');
  });
});
