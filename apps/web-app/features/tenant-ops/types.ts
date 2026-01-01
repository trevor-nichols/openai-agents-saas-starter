import type { TenantAccountOperatorSummary } from '@/types/tenantAccount';

export type TenantLifecycleAction = 'suspend' | 'reactivate' | 'deprovision';

export interface TenantLifecycleIntent {
  action: TenantLifecycleAction;
  tenant: TenantAccountOperatorSummary;
}
