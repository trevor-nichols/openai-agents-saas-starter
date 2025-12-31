import type { TenantAccountStatus } from '@/types/tenantAccount';

import type { TenantStatusFilter } from './constants';
import type { TenantLifecycleAction } from './types';

export function resolveStatusFilter(status: TenantStatusFilter): TenantAccountStatus | undefined {
  return status === 'all' ? undefined : status;
}

export function resolveLifecycleActions(status: TenantAccountStatus): TenantLifecycleAction[] {
  if (status === 'active') return ['suspend', 'deprovision'];
  if (status === 'suspended') return ['reactivate', 'deprovision'];
  return [];
}
