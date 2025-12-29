'use client';

import type { Meta, StoryObj } from '@storybook/react';
import { PlanChangeDialog } from '../components/PlanChangeDialog';
import { mockPlans, mockSubscription } from '../../shared/__stories__/fixtures';

type PlanChangeDialogPreviewProps = {
  open?: boolean;
  isSubmitting?: boolean;
  errorMessage?: string;
  hasSubscription?: boolean;
};

function PlanChangeDialogPreview({
  open = true,
  isSubmitting = false,
  errorMessage,
  hasSubscription = true,
}: PlanChangeDialogPreviewProps) {
  const plan = (mockPlans[1] ?? mockPlans[0])!;

  return (
    <PlanChangeDialog
      open={open}
      plan={plan}
      subscription={hasSubscription ? mockSubscription : null}
      onSubmit={(values) => console.log('submit plan', values)}
      onClose={() => console.log('close dialog')}
      isSubmitting={isSubmitting}
      errorMessage={errorMessage}
    />
  );
}

const meta: Meta<typeof PlanChangeDialogPreview> = {
  title: 'Billing/PlanChangeDialog',
  component: PlanChangeDialogPreview,
};

export default meta;

type Story = StoryObj<typeof PlanChangeDialogPreview>;

export const Default: Story = {};

export const Submitting: Story = {
  args: {
    isSubmitting: true,
  },
};

export const ErrorState: Story = {
  args: {
    errorMessage: 'Subscription update failed',
  },
};

export const NewSubscription: Story = {
  args: {
    hasSubscription: false,
  },
};
