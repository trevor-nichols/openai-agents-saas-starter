export type TenantAccountStatus =
  | 'active'
  | 'suspended'
  | 'deprovisioning'
  | 'deprovisioned';

export interface TenantAccountSummary {
  id: string;
  slug: string;
  name: string;
  status: TenantAccountStatus;
  createdAt: string;
  updatedAt: string;
  statusUpdatedAt: string | null;
  suspendedAt: string | null;
  deprovisionedAt: string | null;
}

export type TenantAccount = TenantAccountSummary;

export interface TenantAccountOperatorSummary extends TenantAccountSummary {
  statusReason: string | null;
  statusUpdatedBy: string | null;
}

export interface TenantAccountListResult {
  accounts: TenantAccountOperatorSummary[];
  total: number;
}

export interface TenantAccountCreateInput {
  name: string;
  slug?: string | null;
}

export interface TenantAccountUpdateInput {
  name?: string | null;
  slug?: string | null;
}

export interface TenantAccountSelfUpdateInput {
  name: string;
}

export interface TenantAccountLifecycleInput {
  reason: string;
}

export interface PlatformTenantListFilters {
  status?: TenantAccountStatus | null;
  q?: string | null;
  limit?: number;
  offset?: number;
}
