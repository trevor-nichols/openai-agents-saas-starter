'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { StatusAlertsCard } from '../StatusAlertsCard';

const meta: Meta<typeof StatusAlertsCard> = {
  title: 'Marketing/Components/StatusAlertsCard',
  component: StatusAlertsCard,
  args: {
    source: 'storybook',
    onLeadSubmit: (payload) => console.log('lead submit', payload),
  },
};

export default meta;

type Story = StoryObj<typeof StatusAlertsCard>;

export const Default: Story = {};
