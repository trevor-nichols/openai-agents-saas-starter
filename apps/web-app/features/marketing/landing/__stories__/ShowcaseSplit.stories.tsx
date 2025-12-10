'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { ShowcaseSplit } from '../components/ShowcaseSplit';
import { showcaseTabs } from './fixtures';

const meta: Meta<typeof ShowcaseSplit> = {
  title: 'Marketing/Landing/ShowcaseSplit',
  component: ShowcaseSplit,
  args: {
    tabs: showcaseTabs,
  },
};

export default meta;

type Story = StoryObj<typeof ShowcaseSplit>;

export const Default: Story = {};

export const Empty: Story = {
  args: {
    tabs: [],
  },
};
