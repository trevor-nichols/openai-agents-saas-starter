import type { ActivityListPage } from '@/types/activity';
import { apiV1Path } from '@/lib/apiPaths';

export async function fetchActivityPage(params?: {
  limit?: number;
  cursor?: string | null;
  action?: string | null;
  actor_id?: string | null;
  object_type?: string | null;
  object_id?: string | null;
  status?: string | null;
}): Promise<ActivityListPage> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set('limit', String(params.limit));
  if (params?.cursor) searchParams.set('cursor', params.cursor);
  if (params?.action) searchParams.set('action', params.action);
  if (params?.actor_id) searchParams.set('actor_id', params.actor_id);
  if (params?.object_type) searchParams.set('object_type', params.object_type);
  if (params?.object_id) searchParams.set('object_id', params.object_id);
  if (params?.status) searchParams.set('status', params.status);

  const response = await fetch(
    `${apiV1Path('/activity')}${searchParams.toString() ? `?${searchParams.toString()}` : ''}`,
    { cache: 'no-store' },
  );

  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as { message?: string };
    throw new Error(payload.message || 'Failed to load activity feed');
  }

  const result = (await response.json()) as ActivityListPage;
  return {
    items: result.items ?? [],
    next_cursor: result.next_cursor ?? null,
    unread_count: result.unread_count ?? 0,
  };
}

export async function markActivityRead(eventId: string): Promise<number> {
  const response = await fetch(`${apiV1Path(`/activity/${eventId}/read`)}`, {
    method: 'POST',
    cache: 'no-store',
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as { message?: string };
    throw new Error(payload.message || 'Failed to mark activity as read');
  }
  const result = (await response.json()) as { unread_count?: number };
  return result.unread_count ?? 0;
}

export async function dismissActivity(eventId: string): Promise<number> {
  const response = await fetch(`${apiV1Path(`/activity/${eventId}/dismiss`)}`, {
    method: 'POST',
    cache: 'no-store',
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as { message?: string };
    throw new Error(payload.message || 'Failed to dismiss activity');
  }
  const result = (await response.json()) as { unread_count?: number };
  return result.unread_count ?? 0;
}

export async function markAllActivityRead(): Promise<number> {
  const response = await fetch(apiV1Path('/activity/mark-all-read'), {
    method: 'POST',
    cache: 'no-store',
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as { message?: string };
    throw new Error(payload.message || 'Failed to mark all activity as read');
  }
  const result = (await response.json()) as { unread_count?: number };
  return result.unread_count ?? 0;
}
