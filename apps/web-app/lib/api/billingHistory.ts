import type { StripeEventStatus } from '@/lib/api/client/types.gen';
import type { BillingEventHistoryResponse } from '@/types/billing';
import { apiV1Path } from '@/lib/apiPaths';

export interface FetchBillingHistoryParams {
  tenantId: string;
  limit?: number;
  cursor?: string | null;
  eventType?: string | null;
  processingStatus?: StripeEventStatus | null;
  signal?: AbortSignal;
}

export async function fetchBillingHistory(params: FetchBillingHistoryParams): Promise<BillingEventHistoryResponse> {
  const { tenantId, limit = 25, cursor, eventType, processingStatus, signal } = params;

  if (!tenantId) {
    throw new Error('Tenant id is required to fetch billing history.');
  }

  const search = new URLSearchParams();
  search.set('limit', String(limit));
  if (cursor) {
    search.set('cursor', cursor);
  }
  if (eventType) {
    search.set('event_type', eventType);
  }
  if (processingStatus) {
    search.set('processing_status', processingStatus);
  }

  const response = await fetch(
    `${apiV1Path(`/billing/tenants/${encodeURIComponent(tenantId)}/events`)}?${search.toString()}`,
    {
      cache: 'no-store',
      signal,
    },
  );

  const payload = (await response.json()) as BillingEventHistoryResponse & { message?: string; error?: string };

  if (response.status === 404) {
    const message = payload?.message || payload?.error || '';
    if (message.toLowerCase().includes('billing is disabled')) {
      return { items: [], next_cursor: null };
    }
    throw new Error(payload?.message || 'Failed to load billing history.');
  }

  if (!response.ok) {
    throw new Error(payload?.message || 'Failed to load billing history.');
  }

  return payload;
}
