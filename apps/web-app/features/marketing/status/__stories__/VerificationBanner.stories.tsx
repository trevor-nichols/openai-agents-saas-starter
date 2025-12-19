'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { VerificationBanner } from '../components/VerificationBanner';
import { mockBanner } from './fixtures';

const meta: Meta<typeof VerificationBanner> = {
  title: 'Marketing/Status/VerificationBanner',
  component: VerificationBanner,
  args: {
    banner: mockBanner,
  },
};

export default meta;

type Story = StoryObj<typeof VerificationBanner>;

export const Default: Story = {};

export const Hidden: Story = {
  args: {
    banner: null,
  },
};
