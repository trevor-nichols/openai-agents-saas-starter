'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { PlanCardGrid } from '../components/PlanCardGrid';
import { mockPlanCards } from './fixtures';

const meta: Meta<typeof PlanCardGrid> = {
  title: 'Marketing/Pricing/PlanCardGrid',
  component: PlanCardGrid,
  args: {
    plans: mockPlanCards,
    primaryCtaHref: '/register',
    onPlanCtaClick: (plan) => console.log('plan click', plan),
  },
};

export default meta;

type Story = StoryObj<typeof PlanCardGrid>;

export const Default: Story = {};
