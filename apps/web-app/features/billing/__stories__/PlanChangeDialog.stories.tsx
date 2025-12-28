'use client';

import type { Meta, StoryObj } from '@storybook/react';
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';

import { PlanChangeDialog } from '../components/PlanChangeDialog';
import type { PlanFormValues } from '../types';
import { mockPlans, resetFormDefaults } from './fixtures';

type PlanChangeDialogPreviewProps = {
  open?: boolean;
  isSubmitting?: boolean;
  errorMessage?: string;
  updateCurrent?: boolean;
};

function PlanChangeDialogPreview({
  open = true,
  isSubmitting = false,
  errorMessage,
  updateCurrent = false,
}: PlanChangeDialogPreviewProps) {
  const plan = (mockPlans[1] ?? mockPlans[0])!;
  const form = useForm<PlanFormValues>({
    defaultValues: {
      billingEmail: '',
      autoRenew: true,
      seatCount: undefined,
      timing: 'auto',
    },
  });

  useEffect(() => {
    resetFormDefaults(form);
  }, [form]);

  return (
    <PlanChangeDialog
      open={open}
      plan={plan}
      mode={updateCurrent ? 'update' : 'change'}
      form={form}
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

export const UpdatingCurrentPlan: Story = {
  args: {
    updateCurrent: true,
  },
};
