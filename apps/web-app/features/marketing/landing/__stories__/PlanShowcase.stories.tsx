'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { PlanShowcase } from '../components/PlanShowcase';
import { plansSnapshot } from './fixtures';

const meta: Meta<typeof PlanShowcase> = {
  title: 'Marketing/Landing/PlanShowcase',
  component: PlanShowcase,
  args: {
    plans: plansSnapshot,
  },
};

export default meta;

type Story = StoryObj<typeof PlanShowcase>;

export const Default: Story = {};

export const Empty: Story = {
  args: {
    plans: [],
  },
};
