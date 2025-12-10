'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { InvoiceCard } from '../components/InvoiceCard';
import { mockInvoiceSummary } from './fixtures';

const meta: Meta<typeof InvoiceCard> = {
  title: 'Billing/InvoiceCard',
  component: InvoiceCard,
  args: {
    summary: mockInvoiceSummary,
    isLoading: false,
  },
};

export default meta;

type Story = StoryObj<typeof InvoiceCard>;

export const Default: Story = {};

export const Loading: Story = {
  args: {
    isLoading: true,
  },
};

export const NoInvoice: Story = {
  args: {
    summary: null,
  },
};
