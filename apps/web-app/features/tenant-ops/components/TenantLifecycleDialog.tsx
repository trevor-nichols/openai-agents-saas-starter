'use client';

import { useEffect, useMemo } from 'react';
import { z } from 'zod';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Textarea } from '@/components/ui/textarea';
import { useAuthForm } from '@/hooks/useAuthForm';
import type { TenantAccountOperatorSummary } from '@/types/tenantAccount';

import type { TenantLifecycleAction } from '../types';

interface TenantLifecycleDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  tenant: TenantAccountOperatorSummary | null;
  action: TenantLifecycleAction | null;
  isSubmitting: boolean;
  onSubmit: (payload: { reason: string }) => Promise<void>;
}

const reasonSchema = z.object({
  reason: z
    .string()
    .min(4, 'Please provide a short reason.')
    .max(280, 'Keep reasons under 280 characters.'),
});

const ACTION_COPY: Record<TenantLifecycleAction, { title: string; description: string; cta: string }> = {
  suspend: {
    title: 'Suspend tenant',
    description: 'Suspending a tenant blocks access to tenant-scoped APIs until reactivated.',
    cta: 'Suspend tenant',
  },
  reactivate: {
    title: 'Reactivate tenant',
    description: 'Reactivating restores access to tenant-scoped APIs.',
    cta: 'Reactivate tenant',
  },
  deprovision: {
    title: 'Deprovision tenant',
    description: 'Deprovisioning revokes access and marks the tenant for cleanup.',
    cta: 'Deprovision tenant',
  },
};

export function TenantLifecycleDialog({
  open,
  onOpenChange,
  tenant,
  action,
  isSubmitting,
  onSubmit,
}: TenantLifecycleDialogProps) {
  const copy = action ? ACTION_COPY[action] : null;

  const { form, onSubmit: handleSubmit } = useAuthForm({
    schema: reasonSchema,
    initialValues: { reason: '' },
    submitHandler: async (values) => {
      await onSubmit({ reason: values.reason.trim() });
      form.reset();
    },
  });

  useEffect(() => {
    if (!open) {
      form.reset();
    }
  }, [open, form]);

  const isDisabled = useMemo(() => !tenant || !action, [tenant, action]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{copy?.title ?? 'Tenant action'}</DialogTitle>
          <DialogDescription>
            {tenant ? (
              <>
                {copy?.description}{' '}
                <span className="font-semibold text-foreground">{tenant.name}</span> ({tenant.slug}).
              </>
            ) : (
              'Select a tenant to continue.'
            )}
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <FormField
              control={form.control}
              name="reason"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Reason</FormLabel>
                  <FormControl>
                    <Textarea {...field} rows={4} placeholder="Provide a short explanation for audit logs." />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={isDisabled || isSubmitting}>
                {isSubmitting ? 'Submitting…' : copy?.cta ?? 'Confirm'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
