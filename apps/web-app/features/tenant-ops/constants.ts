import type { TenantAccountStatus } from '@/types/tenantAccount';

import type { TenantLifecycleAction } from './types';

export type TenantStatusFilter = TenantAccountStatus | 'all';

export const DEFAULT_TENANT_STATUS_FILTER: TenantStatusFilter = 'active';
export const TENANT_PAGE_LIMIT = 25;

export const TENANT_STATUS_LABELS: Record<TenantAccountStatus, string> = {
  provisioning: 'Provisioning',
  active: 'Active',
  suspended: 'Suspended',
  deprovisioning: 'Deprovisioning',
  deprovisioned: 'Deprovisioned',
};

export const TENANT_STATUS_TONES: Record<TenantAccountStatus, 'default' | 'positive' | 'warning'> = {
  provisioning: 'warning',
  active: 'positive',
  suspended: 'warning',
  deprovisioning: 'warning',
  deprovisioned: 'default',
};

export const TENANT_STATUS_OPTIONS: { label: string; value: TenantStatusFilter }[] = [
  { label: 'All statuses', value: 'all' },
  { label: TENANT_STATUS_LABELS.provisioning, value: 'provisioning' },
  { label: TENANT_STATUS_LABELS.active, value: 'active' },
  { label: TENANT_STATUS_LABELS.suspended, value: 'suspended' },
  { label: TENANT_STATUS_LABELS.deprovisioning, value: 'deprovisioning' },
  { label: TENANT_STATUS_LABELS.deprovisioned, value: 'deprovisioned' },
];

export const TENANT_ACTION_RESULT_COPY: Record<TenantLifecycleAction, string> = {
  suspend: 'suspended',
  reactivate: 'reactivated',
  deprovision: 'deprovisioned',
};
