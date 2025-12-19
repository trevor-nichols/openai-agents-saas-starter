'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { BillingContactsCard } from '../components/BillingContactsCard';
import { sampleContacts } from './fixtures';

const meta: Meta<typeof BillingContactsCard> = {
  title: 'Settings/Tenant/Billing Contacts Card',
  component: BillingContactsCard,
  args: {
    contacts: sampleContacts,
    isSaving: false,
    onSubmit: async (next) => {
      console.log('save contacts', next);
    },
  },
};

export default meta;

type Story = StoryObj<typeof BillingContactsCard>;

export const Default: Story = {};

export const Saving: Story = {
  args: {
    isSaving: true,
  },
};

export const EmptyState: Story = {
  args: {
    contacts: [],
  },
};
