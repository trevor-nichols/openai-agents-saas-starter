import { describe, expect, it } from 'vitest';

import type { StatusSubscriptionSummary } from '@/types/statusSubscriptions';

import { applySubscriptionFilters } from '../hooks/useStatusOpsFilters';

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
    channel: 'webhook',
    severityFilter: 'maintenance',
    status: 'pending_verification',
    targetMasked: 'https://hooks.dev/web',
    tenantId: null,
    createdBy: 'bob',
    createdAt: '2025-01-03T00:00:00Z',
    updatedAt: '2025-01-04T00:00:00Z',
  },
];

describe('applySubscriptionFilters', () => {
  it('returns all subscriptions when filters are permissive', () => {
    const result = applySubscriptionFilters(subscriptions, {
      channelFilter: 'all',
      statusFilter: 'all',
      severityFilter: 'any',
      searchTerm: '',
      appliedTenantId: null,
    });

    expect(result).toHaveLength(2);
  });

  it('filters by channel, status, and severity', () => {
    const result = applySubscriptionFilters(subscriptions, {
      channelFilter: 'email',
      statusFilter: 'active',
      severityFilter: 'major',
      searchTerm: '',
      appliedTenantId: null,
    });

    expect(result).toEqual([subscriptions[0]]);
  });

  it('filters by search term and tenant id', () => {
    const result = applySubscriptionFilters(subscriptions, {
      channelFilter: 'all',
      statusFilter: 'all',
      severityFilter: 'any',
      searchTerm: 'bob',
      appliedTenantId: null,
    });

    expect(result).toEqual([subscriptions[1]]);

    const tenantScoped = applySubscriptionFilters(subscriptions, {
      channelFilter: 'all',
      statusFilter: 'all',
      severityFilter: 'any',
      searchTerm: '',
      appliedTenantId: 'tenant-a',
    });

    expect(tenantScoped).toEqual([subscriptions[0]]);
  });
});
