import type { TenantAccount, TenantAccountSelfUpdateInput } from '@/types/tenantAccount';

let tenantAccount: TenantAccount = {
  id: 'tenant-123',
  slug: 'acme',
  name: 'Acme Corporation',
  status: 'active',
  createdAt: '2025-01-15T16:30:00.000Z',
  updatedAt: new Date().toISOString(),
  statusUpdatedAt: null,
  suspendedAt: null,
  deprovisionedAt: null,
};

export async function fetchTenantAccount(): Promise<TenantAccount> {
  return tenantAccount;
}

export function getTenantAccountFixture(): TenantAccount {
  return tenantAccount;
}

export async function updateTenantAccount(
  payload: TenantAccountSelfUpdateInput,
): Promise<TenantAccount> {
  tenantAccount = {
    ...tenantAccount,
    name: payload.name,
    updatedAt: new Date().toISOString(),
  };
  return tenantAccount;
}
