import { describe, expect, it } from 'vitest';

import type { StatusSubscriptionSummary } from '@/types/statusSubscriptions';

import { deriveStatusOpsMetrics } from '../hooks/useStatusOpsMetrics';

const subscriptions: StatusSubscriptionSummary[] = [
  {
    id: 'sub-1',
    channel: 'email',
    severityFilter: 'major',
    status: 'active',
    targetMasked: 'alice@example.com',
    tenantId: 'tenant-a',
    createdBy: 'alice',
    createdAt: '2025-01-01T00:00:00Z',
    updatedAt: '2025-01-02T00:00:00Z',
  },
  {
    id: 'sub-2',
    channel: 'email',
    severityFilter: 'maintenance',
    status: 'pending_verification',
    targetMasked: 'bob@example.com',
    tenantId: 'tenant-b',
    createdBy: 'bob',
    createdAt: '2025-01-03T00:00:00Z',
    updatedAt: '2025-01-04T00:00:00Z',
  },
  {
    id: 'sub-3',
    channel: 'webhook',
    severityFilter: 'all',
    status: 'revoked',
    targetMasked: 'https://hooks.dev/web',
    tenantId: null,
    createdBy: 'carol',
    createdAt: '2025-01-05T00:00:00Z',
    updatedAt: '2025-01-06T00:00:00Z',
  },
];

describe('deriveStatusOpsMetrics', () => {
  it('calculates aggregate metrics correctly', () => {
    const metrics = deriveStatusOpsMetrics(subscriptions);

    expect(metrics).toEqual({
      total: 3,
      active: 1,
      pending: 1,
      emailCount: 2,
      webhookCount: 1,
      tenantCount: 2,
    });
  });
});
