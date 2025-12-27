'use client';

import { useCallback, useState } from 'react';

import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { GlassPanel, SectionHeader } from '@/components/ui/foundation';
import { PasswordInput } from '@/components/ui/password-input';

import { useDisableAccountForm } from '../hooks/useDisableAccountForm';

export function AccountDisableCard() {
  const [open, setOpen] = useState(false);
  const { form, onSubmit, isSaving, rootError } = useDisableAccountForm({
    onSuccess: () => setOpen(false),
  });

  const handleOpenChange = useCallback(
    (nextOpen: boolean) => {
      setOpen(nextOpen);
      if (!nextOpen) {
        form.reset({ currentPassword: '' });
      }
    },
    [form],
  );

  return (
    <GlassPanel className="space-y-6 border border-destructive/30 bg-destructive/5">
      <SectionHeader
        title="Disable account"
        description="Disabling your account revokes all sessions and removes access immediately."
      />

      <Alert variant="destructive">
        <AlertTitle>Permanent access revocation</AlertTitle>
        <AlertDescription className="mt-2">
          This action cannot be undone in the dashboard. If you are the last tenant owner,
          you must transfer ownership before disabling your account.
        </AlertDescription>
      </Alert>

      <AlertDialog open={open} onOpenChange={handleOpenChange}>
        <AlertDialogTrigger asChild>
          <Button variant="destructive">Disable my account</Button>
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Disable your account?</AlertDialogTitle>
            <AlertDialogDescription>
              Confirm your password to disable the account. You will be signed out everywhere.
            </AlertDialogDescription>
          </AlertDialogHeader>

          <Form {...form}>
            <form className="space-y-4" onSubmit={onSubmit} noValidate>
              <FormField
                control={form.control}
                name="currentPassword"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Current password</FormLabel>
                    <FormControl>
                      <PasswordInput {...field} autoComplete="current-password" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {rootError ? (
                <p className="text-sm font-medium text-destructive" role="alert">
                  {rootError}
                </p>
              ) : null}

              <AlertDialogFooter>
                <AlertDialogCancel disabled={isSaving}>Cancel</AlertDialogCancel>
                <Button
                  type="submit"
                  variant="destructive"
                  disabled={isSaving}
                >
                  {isSaving ? 'Disabling...' : 'Disable account'}
                </Button>
              </AlertDialogFooter>
            </form>
          </Form>
        </AlertDialogContent>
      </AlertDialog>
    </GlassPanel>
  );
}
