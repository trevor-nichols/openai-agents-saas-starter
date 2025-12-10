'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { KpiGrid } from '../components/KpiGrid';
import { dashboardKpis } from './fixtures';

const meta: Meta<typeof KpiGrid> = {
  title: 'Dashboard/KpiGrid',
  component: KpiGrid,
};

export default meta;

type Story = StoryObj<typeof KpiGrid>;

export const Default: Story = {
  args: {
    kpis: dashboardKpis,
    isLoading: false,
    error: null,
  },
};

export const Loading: Story = {
  args: {
    kpis: [],
    isLoading: true,
    error: null,
  },
};

export const Error: Story = {
  args: {
    kpis: [],
    isLoading: false,
    error: 'Failed to load KPI data',
  },
};
