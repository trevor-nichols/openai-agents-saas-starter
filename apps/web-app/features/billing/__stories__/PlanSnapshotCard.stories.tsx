'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { PlanSnapshotCard } from '../components/PlanSnapshotCard';
import { mockPlanSnapshot } from './fixtures';

const meta: Meta<typeof PlanSnapshotCard> = {
  title: 'Billing/PlanSnapshotCard',
  component: PlanSnapshotCard,
  args: {
    snapshot: mockPlanSnapshot,
  },
};

export default meta;

type Story = StoryObj<typeof PlanSnapshotCard>;

export const Default: Story = {};

export const ErrorStream: Story = {
  args: {},
};
