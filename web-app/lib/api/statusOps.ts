import type {
  StatusIncidentResendResponse,
  StatusSubscriptionListResponse,
} from '@/lib/api/client/types.gen';
import {
  mapStatusSubscriptionResponse,
  type StatusSubscriptionList,
} from '@/types/statusSubscriptions';

const SUBSCRIPTIONS_ENDPOINT = '/api/status/subscriptions';
const INCIDENT_RESEND_ENDPOINT = (incidentId: string) =>
  `/api/status/incidents/${incidentId}/resend`;

interface ApiEnvelope<T> {
  success?: boolean;
  error?: string;
  items?: StatusSubscriptionListResponse['items'];
  next_cursor?: string | null;
  dispatched?: number;
  issues?: unknown;
}

export interface StatusSubscriptionsFilters {
  limit?: number;
  cursor?: string | null;
  tenantId?: string | null;
}

export async function fetchStatusSubscriptions(
  filters: StatusSubscriptionsFilters = {},
): Promise<StatusSubscriptionList> {
  const search = new URLSearchParams();
  if (filters.limit) search.set('limit', String(filters.limit));
  if (filters.cursor) search.set('cursor', filters.cursor);

  if (filters.tenantId === null) {
    search.set('tenant_id', 'all');
  } else if (typeof filters.tenantId === 'string' && filters.tenantId.trim().length > 0) {
    search.set('tenant_id', filters.tenantId.trim());
  }

  const response = await fetch(
    `${SUBSCRIPTIONS_ENDPOINT}${search.toString() ? `?${search.toString()}` : ''}`,
    { cache: 'no-store' },
  );

  const payload = (await response.json().catch(() => ({}))) as ApiEnvelope<StatusSubscriptionListResponse>;

  if (!response.ok || payload.success !== true) {
    throw new Error(payload.error ?? 'Unable to load status subscriptions.');
  }

  const items = (payload.items ?? []).map(mapStatusSubscriptionResponse);
  return {
    items,
    nextCursor: payload.next_cursor ?? null,
  };
}

export interface ResendIncidentInput {
  incidentId: string;
  severity?: 'all' | 'major' | 'maintenance';
  tenantId?: string | null;
}

export async function resendIncident(
  input: ResendIncidentInput,
): Promise<StatusIncidentResendResponse> {
  if (!input.incidentId) {
    throw new Error('Incident id is required.');
  }

  const response = await fetch(INCIDENT_RESEND_ENDPOINT(input.incidentId), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    cache: 'no-store',
    body: JSON.stringify({
      severity: input.severity,
      tenantId: input.tenantId ?? null,
    }),
  });

  const payload = (await response.json().catch(() => ({}))) as ApiEnvelope<StatusIncidentResendResponse>;

  if (!response.ok || payload.success === false) {
    throw new Error(payload.error ?? 'Unable to resend incident notifications.');
  }

  return {
    dispatched: payload.dispatched ?? 0,
  };
}
