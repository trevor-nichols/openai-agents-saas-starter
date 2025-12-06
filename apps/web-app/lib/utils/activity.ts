import type { ActivityEvent } from '@/types/activity';

export type ActivityDisplayItem = {
  id: string;
  title: string;
  detail: string;
  status: ActivityEvent['status'];
  timestamp: string;
  metadataSummary?: string | null;
  readState?: ActivityEvent['read_state'];
};

/**
 * Merge live + cached activity events, deduping by id and truncating to limit.
 * Cached events override live copies for the same id so read/dismiss state wins.
 */
export function mergeActivityEvents(
  live: ActivityEvent[],
  cached: ActivityEvent[],
  limit: number,
  options?: { includeDismissed?: boolean },
): ActivityEvent[] {
  const includeDismissed = options?.includeDismissed ?? false;
  const byId = new Map<string, ActivityEvent>();

  // First, take live events for recency ordering.
  for (const event of live) {
    if (!includeDismissed && event.read_state === 'dismissed') continue;
    if (byId.size >= limit) break;
    byId.set(event.id, event);
  }

  // Then overlay cached events so authoritative state (read/dismissed) wins.
  for (const event of cached) {
    if (!includeDismissed && event.read_state === 'dismissed') continue;
    if (byId.size >= limit && !byId.has(event.id)) continue;
    byId.set(event.id, event);
  }

  const merged: ActivityEvent[] = [];
  for (const event of byId.values()) {
    merged.push(event);
    if (merged.length >= limit) break;
  }

  return merged;
}

export function humanizeAction(action?: string | null): string {
  if (!action) return 'Activity';
  return action
    .split('.')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

export function summarizeMetadata(
  metadata: Record<string, unknown> | null | undefined,
): string | null {
  if (!metadata) return null;
  const entries = Object.entries(metadata).slice(0, 2);
  if (!entries.length) return null;
  return entries
    .map(([key, value]) => `${key}: ${typeof value === 'string' ? value : JSON.stringify(value)}`)
    .join(' • ');
}

export function toActivityDisplayItem(event: ActivityEvent): ActivityDisplayItem {
  return {
    id: event.id,
    title: humanizeAction(event.action),
    detail: event.object_type
      ? `${event.object_type}${event.object_id ? ` • ${event.object_id}` : ''}`
      : 'General',
    status: event.status,
    timestamp: event.created_at,
    readState: event.read_state,
    metadataSummary: summarizeMetadata(event.metadata),
  } satisfies ActivityDisplayItem;
}
