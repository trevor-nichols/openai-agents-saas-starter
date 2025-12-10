'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { BillingPreview } from '../components/BillingPreview';
import { billingPreviewSummary } from './fixtures';

const meta: Meta<typeof BillingPreview> = {
  title: 'Dashboard/BillingPreview',
  component: BillingPreview,
};

export default meta;

type Story = StoryObj<typeof BillingPreview>;

export const Default: Story = {
  args: {
    preview: billingPreviewSummary,
  },
};

export const EmptyEvents: Story = {
  args: {
    preview: {
      ...billingPreviewSummary,
      latestEvents: [],
    },
  },
};

export const ErrorStream: Story = {
  args: {
    preview: {
      ...billingPreviewSummary,
      streamStatus: 'error',
    },
  },
};
