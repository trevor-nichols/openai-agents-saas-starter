import type { TenantAccount, TenantAccountSelfUpdateInput } from '@/types/tenantAccount';

import { getTenantAccountFixture, updateTenantAccount } from './tenantAccount-api';

type TenantAccountState = 'default' | 'loading' | 'error';

let accountState: TenantAccountState = 'default';
let accountData: TenantAccount | null = getTenantAccountFixture();

export function setTenantAccountState(
  next: TenantAccountState,
  overrides?: Partial<TenantAccount>,
) {
  accountState = next;
  if (overrides) {
    accountData = {
      ...getTenantAccountFixture(),
      ...overrides,
    };
    return;
  }
  if (!accountData) {
    accountData = getTenantAccountFixture();
  }
}

export function useTenantAccountQuery(options?: { enabled?: boolean }) {
  if (options?.enabled === false) {
    return {
      data: null,
      isLoading: false,
      error: null,
      refetch: async () => {},
    };
  }

  if (accountState === 'loading') {
    return {
      data: null,
      isLoading: true,
      error: null,
      refetch: async () => {},
    };
  }

  if (accountState === 'error') {
    return {
      data: null,
      isLoading: false,
      error: new Error('Unable to load tenant account (storybook mock).'),
      refetch: async () => {},
    };
  }

  if (!accountData) {
    return {
      data: null,
      isLoading: true,
      error: null,
      refetch: async () => {},
    };
  }

  return {
    data: accountData,
    isLoading: false,
    error: null,
    refetch: async () => {},
  };
}

export function useUpdateTenantAccountMutation() {
  return {
    isPending: false,
    mutateAsync: async (payload: TenantAccountSelfUpdateInput) => {
      const updated = await updateTenantAccount(payload);
      accountData = updated;
      return updated;
    },
  };
}

export function resetTenantAccountData() {
  accountData = getTenantAccountFixture();
}
