import type { StatusSubscriptionResponse } from '@/lib/api/client/types.gen';

export type StatusSubscriptionStatus = 'pending_verification' | 'active' | 'revoked' | string;
export type StatusSubscriptionChannel = 'email' | 'webhook' | string;
export type StatusSubscriptionSeverity = 'all' | 'major' | 'maintenance' | string;

export interface StatusSubscriptionSummary {
  id: string;
  channel: StatusSubscriptionChannel;
  severityFilter: StatusSubscriptionSeverity;
  status: StatusSubscriptionStatus;
  targetMasked: string;
  tenantId: string | null;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
}

export interface StatusSubscriptionList {
  items: StatusSubscriptionSummary[];
  nextCursor: string | null;
}

export function mapStatusSubscriptionResponse(
  payload: StatusSubscriptionResponse,
): StatusSubscriptionSummary {
  return {
    id: payload.id,
    channel: payload.channel,
    severityFilter: payload.severity_filter,
    status: payload.status,
    targetMasked: payload.target_masked,
    tenantId: payload.tenant_id ?? null,
    createdBy: payload.created_by,
    createdAt: payload.created_at,
    updatedAt: payload.updated_at,
  };
}

export function formatSubscriptionStatus(status: StatusSubscriptionStatus): string {
  const normalized = status.replace(/_/g, ' ').trim();
  return normalized.length > 0
    ? normalized.charAt(0).toUpperCase() + normalized.slice(1)
    : 'Unknown';
}
