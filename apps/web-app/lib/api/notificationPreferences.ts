import type {
  NotificationPreferenceRequest,
  NotificationPreferenceView,
} from '@/lib/api/client/types.gen';
import { apiV1Path } from '@/lib/apiPaths';

async function parseJson<T>(response: Response): Promise<T> {
  try {
    return (await response.json()) as T;
  } catch (_error) {
    throw new Error('Failed to parse response from server.');
  }
}

function buildHeaders(tenantId?: string | null, tenantRole?: string | null): HeadersInit {
  const headers: Record<string, string> = {};
  if (tenantId) headers['X-Tenant-Id'] = tenantId;
  if (tenantRole) headers['X-Tenant-Role'] = tenantRole;
  return headers;
}

export async function listNotificationPreferencesRequest(
  options?: { tenantId?: string | null; tenantRole?: string | null },
): Promise<NotificationPreferenceView[]> {
  const response = await fetch(apiV1Path('/users/notification-preferences'), {
    headers: buildHeaders(options?.tenantId, options?.tenantRole),
    cache: 'no-store',
  });
  const data = await parseJson<NotificationPreferenceView[] | { message?: string }>(response);
  if (!response.ok) {
    throw new Error((data as { message?: string }).message ?? 'Failed to load notification preferences.');
  }
  return data as NotificationPreferenceView[];
}

export async function upsertNotificationPreferenceRequest(
  payload: NotificationPreferenceRequest,
  options?: { tenantId?: string | null; tenantRole?: string | null },
): Promise<NotificationPreferenceView> {
  const response = await fetch(apiV1Path('/users/notification-preferences'), {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      ...buildHeaders(options?.tenantId, options?.tenantRole),
    },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });
  const data = await parseJson<NotificationPreferenceView | { message?: string }>(response);
  if (!response.ok) {
    throw new Error((data as { message?: string }).message ?? 'Failed to save notification preference.');
  }
  return data as NotificationPreferenceView;
}
