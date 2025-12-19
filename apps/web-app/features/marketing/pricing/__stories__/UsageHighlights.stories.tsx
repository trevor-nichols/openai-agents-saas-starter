'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { UsageHighlights } from '../components/UsageHighlights';
import { mockUsageHighlights } from './fixtures';

const meta: Meta<typeof UsageHighlights> = {
  title: 'Marketing/Pricing/UsageHighlights',
  component: UsageHighlights,
  args: {
    highlights: mockUsageHighlights,
  },
};

export default meta;

type Story = StoryObj<typeof UsageHighlights>;

export const Default: Story = {};

export const Empty: Story = {
  args: {
    highlights: [],
  },
};
