'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { IssueInviteDialog } from '../components/IssueInviteDialog';
import { sampleRequest } from './fixtures';

const meta: Meta<typeof IssueInviteDialog> = {
  title: 'Settings/Signup Guardrails/Issue Invite Dialog',
  component: IssueInviteDialog,
  args: {
    open: true,
    onOpenChange: () => {},
    isSubmitting: false,
    defaultEmail: sampleRequest.email,
    requestId: sampleRequest.id,
    onSubmit: async (payload) => {
      console.log('issue invite', payload);
    },
  },
};

export default meta;

type Story = StoryObj<typeof IssueInviteDialog>;

export const Default: Story = {};

export const MultiUse: Story = {
  args: {
    defaultEmail: null,
  },
};

export const Submitting: Story = {
  args: {
    isSubmitting: true,
  },
};
