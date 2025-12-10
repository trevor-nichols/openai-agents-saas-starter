'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { TenantFlagsCard } from '../components/TenantFlagsCard';
import { sampleTenantSettings } from './fixtures';

const meta: Meta<typeof TenantFlagsCard> = {
  title: 'Settings/Tenant/Tenant Flags Card',
  component: TenantFlagsCard,
  args: {
    flags: sampleTenantSettings.flags,
    isSaving: false,
    onSubmit: async (flags) => {
      console.log('save flags', flags);
    },
  },
};

export default meta;

type Story = StoryObj<typeof TenantFlagsCard>;

export const Default: Story = {};

export const Saving: Story = {
  args: {
    isSaving: true,
  },
};

export const CustomFlags: Story = {
  args: {
    flags: {
      ...sampleTenantSettings.flags,
      sandbox_mode: true,
      audit_export: false,
    },
  },
};
