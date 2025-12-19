'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { UsageTable } from '../components/UsageTable';
import { BILLING_COPY } from '../constants';
import { mockUsageRows } from './fixtures';

const meta: Meta<typeof UsageTable> = {
  title: 'Billing/UsageTable',
  component: UsageTable,
  args: {
    title: BILLING_COPY.overview.usageTableTitle,
    rows: mockUsageRows,
    emptyTitle: BILLING_COPY.overview.usageTableEmptyTitle,
    emptyDescription: BILLING_COPY.overview.usageTableEmptyDescription,
    ctaHref: '/billing/usage',
    ctaLabel: BILLING_COPY.overview.usageCtaLabel,
    caption: 'Mirror this table with your own billing pipeline.',
  },
};

export default meta;

type Story = StoryObj<typeof UsageTable>;

export const Default: Story = {};

export const Empty: Story = {
  args: {
    rows: [],
  },
};

export const Skeleton: Story = {
  args: {
    showSkeleton: true,
  },
};
