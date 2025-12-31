'use client';

import type { BaseSyntheticEvent } from 'react';
import type { UseFormReturn } from 'react-hook-form';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { GlassPanel, PasswordPolicyList, SectionHeader } from '@/components/ui/foundation';
import { PasswordInput } from '@/components/ui/password-input';
import { PASSWORD_POLICY_RULES } from '@/lib/auth/passwordPolicy';
import type { PasswordFormValues } from '../hooks/usePasswordChangeForm';

interface PasswordChangeCardProps {
  form: UseFormReturn<PasswordFormValues>;
  onSubmit: (event?: BaseSyntheticEvent) => void | Promise<void>;
  isSaving: boolean;
  rootError: string | null;
}

export function PasswordChangeCard({ form, onSubmit, isSaving, rootError }: PasswordChangeCardProps) {
  return (
    <GlassPanel className="space-y-6">
      <SectionHeader
        title="Password & sign-in"
        description="Update your password. We’ll sign out other sessions automatically."
      />
      <Form {...form}>
        <form className="space-y-4" onSubmit={onSubmit} noValidate>
          <div className="grid gap-4 md:grid-cols-2">
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

            <FormField
              control={form.control}
              name="newPassword"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>New password</FormLabel>
                  <FormControl>
                    <PasswordInput {...field} autoComplete="new-password" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <FormField
              control={form.control}
              name="confirmNewPassword"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Confirm new password</FormLabel>
                  <FormControl>
                    <PasswordInput {...field} autoComplete="new-password" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          {rootError ? (
            <p className="text-sm font-medium text-destructive" role="alert">
              {rootError}
            </p>
          ) : null}

          <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <PasswordPolicyList items={PASSWORD_POLICY_RULES} />
            <Button className="md:w-auto" type="submit" disabled={isSaving}>
              {isSaving ? 'Saving...' : 'Update password'}
            </Button>
          </div>
        </form>
      </Form>
    </GlassPanel>
  );
}
