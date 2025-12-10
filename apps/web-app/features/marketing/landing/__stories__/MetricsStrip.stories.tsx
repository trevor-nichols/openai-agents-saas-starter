'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { MetricsStrip } from '../components/MetricsStrip';
import { landingMetrics } from './fixtures';

const meta: Meta<typeof MetricsStrip> = {
  title: 'Marketing/Landing/MetricsStrip',
  component: MetricsStrip,
  args: {
    metrics: landingMetrics,
    isLoading: false,
  },
};

export default meta;

type Story = StoryObj<typeof MetricsStrip>;

export const Default: Story = {};

export const Loading: Story = {
  args: {
    isLoading: true,
  },
};
