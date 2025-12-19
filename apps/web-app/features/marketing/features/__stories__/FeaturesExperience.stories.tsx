'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { FeaturesExperience } from '../FeaturesExperience';

const meta: Meta<typeof FeaturesExperience> = {
  title: 'Marketing/Features/Page',
  component: FeaturesExperience,
};

export default meta;

type Story = StoryObj<typeof FeaturesExperience>;

export const Default: Story = {};
