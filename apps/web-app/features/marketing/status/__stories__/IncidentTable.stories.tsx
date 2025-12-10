'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { IncidentTable } from '../components/IncidentTable';
import { mockStatus } from './fixtures';

const meta: Meta<typeof IncidentTable> = {
  title: 'Marketing/Status/IncidentTable',
  component: IncidentTable,
  args: {
    incidents: mockStatus.incidents,
    showSkeletons: false,
  },
};

export default meta;

type Story = StoryObj<typeof IncidentTable>;

export const Default: Story = {};

export const Loading: Story = {
  args: {
    showSkeletons: true,
    incidents: [],
  },
};

export const Empty: Story = {
  args: {
    incidents: [],
    showSkeletons: false,
  },
};
