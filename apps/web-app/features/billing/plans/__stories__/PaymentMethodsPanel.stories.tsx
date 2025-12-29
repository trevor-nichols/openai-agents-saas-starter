'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { PaymentMethodsPanelContent } from '../components/PaymentMethodsPanelContent';
import { mockPaymentMethods } from '../../shared/__stories__/fixtures';

const meta: Meta<typeof PaymentMethodsPanelContent> = {
  title: 'Billing/PaymentMethodsPanel',
  component: PaymentMethodsPanelContent,
  args: {
    paymentMethods: mockPaymentMethods,
    isLoading: false,
    error: null,
    onRetry: async () => {},
    onAdd: () => {},
    onSetDefault: () => {},
    onRequestDetach: () => {},
    isAdding: false,
    stripeEnabled: true,
    canAdd: true,
    isSettingDefaultId: null,
    isDetachingId: null,
  },
};

export default meta;

type Story = StoryObj<typeof PaymentMethodsPanelContent>;

export const Default: Story = {};

export const Loading: Story = {
  args: {
    isLoading: true,
  },
};

export const Empty: Story = {
  args: {
    paymentMethods: [],
  },
};

export const ErrorState: Story = {
  args: {
    error: 'Failed to load payment methods.',
  },
};

export const StripeMissing: Story = {
  args: {
    stripeEnabled: false,
    canAdd: false,
  },
};
