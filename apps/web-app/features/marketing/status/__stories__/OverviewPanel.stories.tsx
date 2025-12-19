'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { OverviewPanel } from '../components/OverviewPanel';
import { mockStatus } from './fixtures';

const meta: Meta<typeof OverviewPanel> = {
  title: 'Marketing/Status/OverviewPanel',
  component: OverviewPanel,
  args: {
    description: mockStatus.overview.description,
  },
};

export default meta;

type Story = StoryObj<typeof OverviewPanel>;

export const Default: Story = {};

export const WithFallbackCopy: Story = {
  args: {
    description: null,
  },
};
