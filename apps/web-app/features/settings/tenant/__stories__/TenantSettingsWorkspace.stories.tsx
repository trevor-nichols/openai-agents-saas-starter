'use client';

import type { Decorator, Meta, StoryObj } from '@storybook/react';

import { TenantSettingsWorkspace } from '../TenantSettingsWorkspace';
import {
  resetTenantAccountData,
  setTenantAccountState,
} from '@/.storybook/mocks/tenantAccount-queries';

const meta: Meta<typeof TenantSettingsWorkspace> = {
  title: 'Settings/Tenant/Workspace',
  component: TenantSettingsWorkspace,
};

export default meta;

type Story = StoryObj<typeof TenantSettingsWorkspace>;

const withTenantAccountState = (state: 'default' | 'loading' | 'error'): Decorator => {
  const DecoratorWithState: Decorator = function TenantAccountStateDecorator(StoryComponent) {
    resetTenantAccountData();
    setTenantAccountState(state);
    return <StoryComponent />;
  };
  return DecoratorWithState;
};

export const BillingEnabled: Story = {
  args: {
    canManageBilling: true,
    canManageTenantSettings: true,
    canManageTenantAccount: true,
  },
  decorators: [withTenantAccountState('default')],
};

export const BillingRestricted: Story = {
  args: {
    canManageBilling: false,
    canManageTenantSettings: true,
    canManageTenantAccount: true,
  },
  decorators: [withTenantAccountState('default')],
};

export const TenantAccountLoading: Story = {
  args: {
    canManageBilling: true,
    canManageTenantSettings: true,
    canManageTenantAccount: true,
  },
  decorators: [withTenantAccountState('loading')],
};

export const TenantAccountError: Story = {
  args: {
    canManageBilling: true,
    canManageTenantSettings: true,
    canManageTenantAccount: true,
  },
  decorators: [withTenantAccountState('error')],
};

export const SettingsAccessRestricted: Story = {
  args: {
    canManageBilling: false,
    canManageTenantSettings: false,
    canManageTenantAccount: false,
  },
  decorators: [withTenantAccountState('default')],
};

export const BillingScopeLimitedAccount: Story = {
  args: {
    canManageBilling: true,
    canManageTenantSettings: true,
    canManageTenantAccount: false,
  },
  decorators: [withTenantAccountState('default')],
};
