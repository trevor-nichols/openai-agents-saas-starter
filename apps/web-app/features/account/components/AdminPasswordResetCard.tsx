// File Path: features/account/components/AdminPasswordResetCard.tsx
// Description: Operator-facing card and dialog to trigger scoped admin password resets.

'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { GlassPanel, InlineTag, PasswordPolicyList, SectionHeader } from '@/components/ui/foundation';
import { Input } from '@/components/ui/input';
import { useToast } from '@/components/ui/use-toast';
import { useAdminResetPasswordMutation } from '@/lib/queries/accountSecurity';
import { PASSWORD_POLICY_RULES } from '../constants';

const adminResetSchema = z
  .object({
    userId: z
      .string()
      .trim()
      .min(1, 'Target user ID is required.')
      .refine((value) => value.length > 0, { message: 'Target user ID is required.' }),
    newPassword: z
      .string()
      .min(14, 'New password must be at least 14 characters.')
      .refine(
        (value) =>
          /[a-z]/.test(value) &&
          /[A-Z]/.test(value) &&
          /[0-9]/.test(value) &&
          /[^A-Za-z0-9]/.test(value),
        {
          message: 'Include upper, lower, number, and symbol.',
        },
      ),
    confirmNewPassword: z.string().min(1, 'Confirm the new password.'),
  })
  .refine((values) => values.newPassword === values.confirmNewPassword, {
    path: ['confirmNewPassword'],
    message: 'Passwords must match.',
  });

type AdminResetFormValues = z.infer<typeof adminResetSchema>;

interface AdminPasswordResetCardProps {
  tenantName?: string | null;
}

export function AdminPasswordResetCard({ tenantName }: AdminPasswordResetCardProps) {
  const [open, setOpen] = useState(false);
  const toast = useToast();
  const mutation = useAdminResetPasswordMutation();

  const form = useForm<AdminResetFormValues>({
    resolver: zodResolver(adminResetSchema),
    defaultValues: {
      userId: '',
      newPassword: '',
      confirmNewPassword: '',
    },
  });

  const handleSubmit = form.handleSubmit(async (values) => {
    form.clearErrors('root');
    try {
      await mutation.mutateAsync({
        user_id: values.userId.trim(),
        new_password: values.newPassword,
      });
      toast.success({
        title: 'Password reset issued',
        description: 'We revoked active sessions for that user and logged the reset.',
      });
      form.reset();
      setOpen(false);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to reset password.';
      form.setError('root', { message });
      toast.error({
        title: 'Reset failed',
        description: message,
      });
    }
  });

  const pending = mutation.isPending;

  return (
    <GlassPanel className="space-y-5">
      <SectionHeader
        title="Admin password reset"
        eyebrow="Operator"
        description="Assist locked-out members without bypassing password policy. Action is tenant-scoped and audit logged."
        actions={<InlineTag tone="warning">Requires support:read</InlineTag>}
      />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-sm text-foreground/70">
          Target users must belong to the current tenant{tenantName ? ` (${tenantName})` : ''}. All active
          sessions are revoked after the reset.
        </div>
        <Button onClick={() => setOpen(true)} size="sm">
          Reset user password
        </Button>
      </div>

      <Alert className="border border-primary/30 bg-primary/5 text-foreground">
        <AlertTitle>Compliance-friendly</AlertTitle>
        <AlertDescription>
          Resets honor the same password policy enforced in the auth service. Events are recorded for audit reviews and
          the user must sign in with the new credential immediately.
        </AlertDescription>
      </Alert>

      <Dialog
        open={open}
        onOpenChange={(nextOpen) => {
          setOpen(nextOpen);
          if (!nextOpen) {
            form.reset();
            form.clearErrors();
          }
        }}
      >
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Reset a tenant user password</DialogTitle>
            <DialogDescription>
              Provide the target user ID and a compliant password. Sessions are revoked once the reset succeeds.
            </DialogDescription>
          </DialogHeader>

          <Form {...form}>
            <form className="space-y-4" onSubmit={handleSubmit} noValidate>
              <FormField
                control={form.control}
                name="userId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>User ID (UUID)</FormLabel>
                    <FormControl>
                      <Input {...field} placeholder="c0ffee00-1234-5678-90ab-feedface0001" autoComplete="off" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="newPassword"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>New password</FormLabel>
                    <FormControl>
                      <Input {...field} type="password" autoComplete="new-password" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="confirmNewPassword"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Confirm new password</FormLabel>
                    <FormControl>
                      <Input {...field} type="password" autoComplete="new-password" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <PasswordPolicyList items={PASSWORD_POLICY_RULES} />

              {form.formState.errors.root ? (
                <p className="text-sm font-medium text-destructive" role="alert">
                  {form.formState.errors.root.message}
                </p>
              ) : null}

              <DialogFooter className="gap-2 sm:justify-end">
                <Button type="button" variant="ghost" onClick={() => setOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={pending}>
                  {pending ? 'Resetting...' : 'Reset password'}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
    </GlassPanel>
  );
}
