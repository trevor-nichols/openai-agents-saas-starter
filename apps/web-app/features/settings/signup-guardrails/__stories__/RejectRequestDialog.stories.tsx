'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { RejectRequestDialog } from '../components/RejectRequestDialog';
import { sampleRequest } from './fixtures';

const meta: Meta<typeof RejectRequestDialog> = {
  title: 'Settings/Signup Guardrails/Reject Request Dialog',
  component: RejectRequestDialog,
  args: {
    open: true,
    onOpenChange: () => {},
    request: sampleRequest,
    isSubmitting: false,
    onSubmit: async (payload) => {
      console.log('reject', payload);
    },
  },
};

export default meta;

type Story = StoryObj<typeof RejectRequestDialog>;

export const Default: Story = {};

export const Submitting: Story = {
  args: {
    isSubmitting: true,
  },
};

export const NoRequestSelected: Story = {
  args: {
    request: null,
  },
};
