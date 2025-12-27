'use client';

import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { GlassPanel, InlineTag, SectionHeader } from '@/components/ui/foundation';
import { Input } from '@/components/ui/input';
import { PasswordInput } from '@/components/ui/password-input';
import type { CurrentUserProfileResponseData } from '@/lib/api/client/types.gen';

import { useEmailChangeForm } from '../hooks/useEmailChangeForm';

interface EmailChangeCardProps {
  profile: CurrentUserProfileResponseData | null;
}

export function EmailChangeCard({ profile }: EmailChangeCardProps) {
  const { form, onSubmit, isSaving, rootError } = useEmailChangeForm(profile);

  return (
    <GlassPanel className="space-y-6">
      <SectionHeader
        title="Email address"
        description="Update your sign-in email. We will require verification and sign you out."
        actions={
          <InlineTag tone={profile?.email_verified ? 'positive' : 'warning'}>
            {profile?.email_verified ? 'Verified' : 'Unverified'}
          </InlineTag>
        }
      />

      <Form {...form}>
        <form className="space-y-4" onSubmit={onSubmit} noValidate>
          <FormField
            control={form.control}
            name="newEmail"
            render={({ field }) => (
              <FormItem>
                <FormLabel>New email</FormLabel>
                <FormControl>
                  <Input
                    {...field}
                    type="email"
                    inputMode="email"
                    autoComplete="email"
                    placeholder="you@example.com"
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

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

          <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <p className="text-xs text-foreground/60">
              Current email: <span className="font-medium text-foreground">{profile?.email ?? 'Unknown'}</span>
            </p>
            <Button type="submit" className="md:w-auto" disabled={isSaving || !profile}>
              {isSaving ? 'Updating...' : 'Change email'}
            </Button>
          </div>
        </form>
      </Form>
    </GlassPanel>
  );
}
