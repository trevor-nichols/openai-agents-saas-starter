'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { StatusOpsStatsRow } from '../components/StatusOpsStatsRow';
import { mockMetrics } from './fixtures';

const meta: Meta<typeof StatusOpsStatsRow> = {
  title: 'Status Ops/StatsRow',
  component: StatusOpsStatsRow,
  args: {
    metrics: mockMetrics,
    appliedTenantId: 'tenant-001',
  },
};

export default meta;

type Story = StoryObj<typeof StatusOpsStatsRow>;

export const Default: Story = {};

export const GlobalScope: Story = {
  args: {
    appliedTenantId: null,
  },
};
