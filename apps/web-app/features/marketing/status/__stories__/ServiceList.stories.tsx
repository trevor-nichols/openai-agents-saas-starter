'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { ServiceList } from '../components/ServiceList';
import { mockStatus } from './fixtures';

const meta: Meta<typeof ServiceList> = {
  title: 'Marketing/Status/ServiceList',
  component: ServiceList,
  args: {
    services: mockStatus.services,
    showSkeletons: false,
  },
};

export default meta;

type Story = StoryObj<typeof ServiceList>;

export const Default: Story = {};

export const Loading: Story = {
  args: {
    showSkeletons: true,
    services: [],
  },
};
