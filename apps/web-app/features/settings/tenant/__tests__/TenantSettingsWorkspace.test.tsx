import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { TenantSettingsWorkspace } from '../TenantSettingsWorkspace';
import type { TenantAccount } from '@/types/tenantAccount';
import type { TenantSettings } from '@/types/tenantSettings';

type TenantSettingsQueryResult = {
  data: TenantSettings | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
};

type TenantAccountQueryResult = {
  data: TenantAccount | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
};

type UseTenantSettingsQueryFn = (options?: { enabled?: boolean }) => TenantSettingsQueryResult;
type UseTenantAccountQueryFn = (options?: { enabled?: boolean }) => TenantAccountQueryResult;

const mockUseTenantSettingsQuery = vi.hoisted(() => vi.fn<UseTenantSettingsQueryFn>());

const mockUseTenantAccountQuery = vi.hoisted(() => vi.fn<UseTenantAccountQueryFn>());

vi.mock('@/lib/queries/tenantSettings', () => ({
  useTenantSettingsQuery: mockUseTenantSettingsQuery,
  useUpdateTenantSettingsMutation: () => ({
    isPending: false,
    mutateAsync: vi.fn(),
  }),
}));

vi.mock('@/lib/queries/tenantAccount', () => ({
  useTenantAccountQuery: mockUseTenantAccountQuery,
  useUpdateTenantAccountMutation: () => ({
    isPending: false,
    mutateAsync: vi.fn(),
  }),
}));

describe('TenantSettingsWorkspace', () => {
  const baseSettingsState: TenantSettingsQueryResult = {
    data: null,
    isLoading: false,
    error: null,
    refetch: async () => {},
  };
  const baseAccountState: TenantAccountQueryResult = {
    data: null,
    isLoading: false,
    error: null,
    refetch: async () => {},
  };

  beforeEach(() => {
    mockUseTenantSettingsQuery.mockReset();
    mockUseTenantAccountQuery.mockReset();
    mockUseTenantSettingsQuery.mockReturnValue(baseSettingsState);
    mockUseTenantAccountQuery.mockReturnValue(baseAccountState);
  });

  it('renders the settings access restricted state when permissions are missing', () => {
    render(
      <TenantSettingsWorkspace
        canManageBilling={false}
        canManageTenantSettings={false}
        canManageTenantAccount={false}
      />,
    );

    expect(screen.getByText('Tenant settings access restricted')).toBeInTheDocument();
    expect(mockUseTenantSettingsQuery).toHaveBeenCalledWith({ enabled: false });
    expect(mockUseTenantAccountQuery).toHaveBeenCalledWith({ enabled: false });
  });

  it('allows billing scoped users to access settings while restricting tenant account edits', () => {
    mockUseTenantSettingsQuery.mockReturnValue({
      data: {
        tenantId: 'tenant-123',
        billingContacts: [],
        billingWebhookUrl: null,
        planMetadata: {},
        flags: {},
        version: 1,
        updatedAt: null,
      },
      isLoading: false,
      error: null,
      refetch: async () => {},
    });

    render(
      <TenantSettingsWorkspace
        canManageBilling={true}
        canManageTenantSettings={true}
        canManageTenantAccount={false}
      />,
    );

    expect(screen.queryByText('Tenant settings access restricted')).not.toBeInTheDocument();
    expect(screen.getByText('Tenant account access restricted')).toBeInTheDocument();
    expect(screen.getByText('Billing contacts')).toBeInTheDocument();
    expect(mockUseTenantSettingsQuery).toHaveBeenCalledWith({ enabled: true });
    expect(mockUseTenantAccountQuery).toHaveBeenCalledWith({ enabled: false });
  });
});
