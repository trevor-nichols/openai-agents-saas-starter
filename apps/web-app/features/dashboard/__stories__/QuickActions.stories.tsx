'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { QuickActions } from '../components/QuickActions';
import { quickActions } from './fixtures';

const meta: Meta<typeof QuickActions> = {
  title: 'Dashboard/QuickActions',
  component: QuickActions,
};

export default meta;

type Story = StoryObj<typeof QuickActions>;

export const Default: Story = {
  args: {
    actions: quickActions,
  },
};
