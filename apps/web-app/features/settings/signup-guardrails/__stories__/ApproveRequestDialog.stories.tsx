'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { ApproveRequestDialog } from '../components/ApproveRequestDialog';
import { sampleRequest } from './fixtures';

const meta: Meta<typeof ApproveRequestDialog> = {
  title: 'Settings/Signup Guardrails/Approve Request Dialog',
  component: ApproveRequestDialog,
  args: {
    open: true,
    onOpenChange: () => {},
    request: sampleRequest,
    isSubmitting: false,
    onSubmit: async (payload) => {
      console.log('approve', payload);
    },
  },
};

export default meta;

type Story = StoryObj<typeof ApproveRequestDialog>;

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
