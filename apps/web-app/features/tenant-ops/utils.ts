import type { TenantAccountStatus } from '@/types/tenantAccount';

import type { TenantLifecycleAction } from './types';

export function resolveLifecycleActions(status: TenantAccountStatus): TenantLifecycleAction[] {
  if (status === 'active') return ['suspend', 'deprovision'];
  if (status === 'suspended') return ['reactivate', 'deprovision'];
  return [];
}
