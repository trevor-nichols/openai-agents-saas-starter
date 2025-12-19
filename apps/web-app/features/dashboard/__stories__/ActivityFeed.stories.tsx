'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { ActivityFeed } from '../components/ActivityFeed';
import { activityItems } from './fixtures';

const meta: Meta<typeof ActivityFeed> = {
  title: 'Dashboard/ActivityFeed',
  component: ActivityFeed,
  args: {
    onRefresh: () => console.log('refresh activity'),
  },
};

export default meta;

type Story = StoryObj<typeof ActivityFeed>;

export const Default: Story = {
  args: {
    items: activityItems,
    isLoading: false,
    error: null,
  },
};

export const Loading: Story = {
  args: {
    items: [],
    isLoading: true,
    error: null,
  },
};

export const Empty: Story = {
  args: {
    items: [],
    isLoading: false,
    error: null,
  },
};

export const Error: Story = {
  args: {
    items: [],
    isLoading: false,
    error: 'Audit log unavailable',
  },
};
