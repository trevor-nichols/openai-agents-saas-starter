import type { ActivityEvent } from '@/types/activity';

export type ActivityDisplayItem = {
  id: string;
  title: string;
  detail: string;
  status: ActivityEvent['status'];
  timestamp: string;
  metadataSummary?: string | null;
};

/**
 * Merge live + cached activity events, deduping by id and truncating to limit.
 * Live events are preferred when duplicates exist.
 */
export function mergeActivityEvents(
  live: ActivityEvent[],
  cached: ActivityEvent[],
  limit: number,
): ActivityEvent[] {
  const seen = new Set<string>();
  const merged: ActivityEvent[] = [];

  for (const event of [...live, ...cached]) {
    if (seen.has(event.id)) continue;
    seen.add(event.id);
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
    metadataSummary: summarizeMetadata(event.metadata),
  } satisfies ActivityDisplayItem;
}
