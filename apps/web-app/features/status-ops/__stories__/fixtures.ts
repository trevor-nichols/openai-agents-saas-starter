import { deriveStatusOpsMetrics } from '../hooks/useStatusOpsMetrics';
import type { IncidentRecord } from '@/types/status';
import type { StatusSubscriptionSummary } from '@/types/statusSubscriptions';

export const mockSubscriptions: StatusSubscriptionSummary[] = [
  {
    id: 'sub-active-email',
    channel: 'email',
    severityFilter: 'major',
    status: 'active',
    targetMasked: 'sre-team@acme.io',
    tenantId: 'tenant-001',
    createdBy: 'alice@example.com',
    createdAt: '2025-12-01T10:00:00Z',
    updatedAt: '2025-12-05T09:15:00Z',
  },
  {
    id: 'sub-pending-webhook',
    channel: 'webhook',
    severityFilter: 'all',
    status: 'pending_verification',
    targetMasked: 'https://hooks.acme.io/status',
    tenantId: null,
    createdBy: 'automation',
    createdAt: '2025-11-20T14:30:00Z',
    updatedAt: '2025-11-21T08:00:00Z',
  },
  {
    id: 'sub-revoked-email',
    channel: 'email',
    severityFilter: 'maintenance',
    status: 'revoked',
    targetMasked: 'status@vendor.net',
    tenantId: 'tenant-002',
    createdBy: 'bob@example.com',
    createdAt: '2025-10-11T16:20:00Z',
    updatedAt: '2025-10-11T16:20:00Z',
  },
  {
    id: 'sub-active-webhook',
    channel: 'webhook',
    severityFilter: 'major',
    status: 'active',
    targetMasked: 'https://alerts.status.acme/internal',
    tenantId: 'tenant-003',
    createdBy: 'platform-bot',
    createdAt: '2025-12-08T09:00:00Z',
    updatedAt: '2025-12-09T09:00:00Z',
  },
  {
    id: 'sub-active-global',
    channel: 'email',
    severityFilter: 'all',
    status: 'active',
    targetMasked: 'oncall@acme.io',
    tenantId: null,
    createdBy: 'ops@example.com',
    createdAt: '2025-12-09T07:45:00Z',
    updatedAt: '2025-12-09T07:45:00Z',
  },
];

export const mockIncidents: IncidentRecord[] = [
  {
    id: 'inc-rt-outage',
    service: 'Realtime API',
    occurredAt: '2025-12-09T13:10:00Z',
    impact: 'partial outage',
    state: 'monitoring',
  },
  {
    id: 'inc-billing-delay',
    service: 'Billing pipeline',
    occurredAt: '2025-12-08T22:00:00Z',
    impact: 'delayed notifications',
    state: 'resolved',
  },
  {
    id: 'inc-maintenance',
    service: 'Platform maintenance',
    occurredAt: '2025-12-07T06:30:00Z',
    impact: 'planned maintenance',
    state: 'in_progress',
  },
];

export const mockMetrics = deriveStatusOpsMetrics(mockSubscriptions);
export const defaultTenantId = 'tenant-001';
