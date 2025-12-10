'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { ShowcaseTabs } from '../components/ShowcaseTabs';
import { SHOWCASE_TABS } from '../constants';

const meta: Meta<typeof ShowcaseTabs> = {
  title: 'Marketing/Features/ShowcaseTabs',
  component: ShowcaseTabs,
  args: {
    tabs: SHOWCASE_TABS,
  },
};

export default meta;

type Story = StoryObj<typeof ShowcaseTabs>;

export const Default: Story = {};
