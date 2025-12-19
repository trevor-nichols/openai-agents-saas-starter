'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { LandingExperience } from '../LandingExperience';

const meta: Meta<typeof LandingExperience> = {
  title: 'Marketing/Landing/Page',
  component: LandingExperience,
};

export default meta;

type Story = StoryObj<typeof LandingExperience>;

export const Default: Story = {};
