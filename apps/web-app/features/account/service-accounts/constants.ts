import type { ServiceAccountStatusFilter } from '@/types/serviceAccounts';

export const SERVICE_ACCOUNT_DEFAULT_LIMIT = 50;

export const SERVICE_ACCOUNT_STATUS_OPTIONS: { label: string; value: ServiceAccountStatusFilter }[] = [
  { label: 'Active', value: 'active' },
  { label: 'Revoked', value: 'revoked' },
  { label: 'All', value: 'all' },
];
