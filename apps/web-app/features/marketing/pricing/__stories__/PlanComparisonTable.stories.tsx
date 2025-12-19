'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { PlanComparisonTable } from '../components/PlanComparisonTable';
import { mockPlans, mockComparisonRows } from './fixtures';

const meta: Meta<typeof PlanComparisonTable> = {
  title: 'Marketing/Pricing/PlanComparisonTable',
  component: PlanComparisonTable,
  args: {
    plans: mockPlans,
    rows: mockComparisonRows,
  },
};

export default meta;

type Story = StoryObj<typeof PlanComparisonTable>;

export const Default: Story = {};
