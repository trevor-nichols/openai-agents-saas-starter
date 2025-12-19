'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { MetricsPanel } from '../components/MetricsPanel';
import { mockStatus } from './fixtures';

const meta: Meta<typeof MetricsPanel> = {
  title: 'Marketing/Status/MetricsPanel',
  component: MetricsPanel,
  args: {
    metrics: mockStatus.uptimeMetrics,
    showSkeletons: false,
  },
};

export default meta;

type Story = StoryObj<typeof MetricsPanel>;

export const Default: Story = {};

export const Loading: Story = {
  args: {
    showSkeletons: true,
    metrics: [],
  },
};
