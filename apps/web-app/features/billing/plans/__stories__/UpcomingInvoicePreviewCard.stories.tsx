'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { UpcomingInvoicePreviewCardContent } from '../components/UpcomingInvoicePreviewCard';
import { mockUpcomingInvoicePreview } from '../../shared/__stories__/fixtures';

const meta: Meta<typeof UpcomingInvoicePreviewCardContent> = {
  title: 'Billing/UpcomingInvoicePreviewCard',
  component: UpcomingInvoicePreviewCardContent,
  args: {
    preview: mockUpcomingInvoicePreview,
    isLoading: false,
    error: null,
    onRetry: () => {},
    enabled: true,
  },
};

export default meta;

type Story = StoryObj<typeof UpcomingInvoicePreviewCardContent>;

export const Default: Story = {};

export const Loading: Story = {
  args: {
    isLoading: true,
  },
};

export const Empty: Story = {
  args: {
    preview: null,
  },
};

export const ErrorState: Story = {
  args: {
    error: 'Unable to load preview',
  },
};

export const Disabled: Story = {
  args: {
    enabled: false,
    preview: null,
  },
};
