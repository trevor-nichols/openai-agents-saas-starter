'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { MetricsRow } from '../components/MetricsRow';
import { mockMetrics } from './fixtures';

const meta: Meta<typeof MetricsRow> = {
  title: 'Marketing/Features/MetricsRow',
  component: MetricsRow,
  args: {
    metrics: mockMetrics,
  },
};

export default meta;

type Story = StoryObj<typeof MetricsRow>;

export const Default: Story = {};
