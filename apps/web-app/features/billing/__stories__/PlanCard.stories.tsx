'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { PlanCard } from '../components/PlanCard';
import { mockPlans } from './fixtures';

const meta: Meta<typeof PlanCard> = {
  title: 'Billing/PlanCard',
  component: PlanCard,
  args: {
    plan: mockPlans[0],
    current: false,
    disabled: false,
    onSelect: () => console.log('select plan'),
  },
};

export default meta;

type Story = StoryObj<typeof PlanCard>;

export const Starter: Story = {};

export const CurrentPlan: Story = {
  args: {
    plan: mockPlans[1],
    current: true,
  },
};

export const DisabledPlan: Story = {
  args: {
    plan: mockPlans[2],
    disabled: true,
  },
};
