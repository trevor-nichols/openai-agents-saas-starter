'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { PricingExperience } from '../PricingExperience';

const meta: Meta<typeof PricingExperience> = {
  title: 'Marketing/Pricing/Page',
  component: PricingExperience,
};

export default meta;

type Story = StoryObj<typeof PricingExperience>;

export const Default: Story = {};
