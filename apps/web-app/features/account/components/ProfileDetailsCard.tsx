'use client';

import { useMemo } from 'react';

import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { GlassPanel, SectionHeader } from '@/components/ui/foundation';
import { Input } from '@/components/ui/input';
import type { CurrentUserProfileResponseData } from '@/lib/api/client/types.gen';

import { useProfileUpdateForm } from '../hooks/useProfileUpdateForm';
import { PROFILE_FIELD_LIMITS } from '../constants';

interface ProfileDetailsCardProps {
  profile: CurrentUserProfileResponseData | null;
}

export function ProfileDetailsCard({ profile }: ProfileDetailsCardProps) {
  const { form, onSubmit, isSaving, rootError } = useProfileUpdateForm(profile);

  const suggestedTimezone = useMemo(() => {
    try {
      return Intl.DateTimeFormat().resolvedOptions().timeZone ?? 'UTC';
    } catch {
      return 'UTC';
    }
  }, []);

  const suggestedLocale = useMemo(() => {
    if (typeof navigator !== 'undefined' && navigator.language) {
      return navigator.language;
    }
    return 'en-US';
  }, []);

  return (
    <GlassPanel className="space-y-6">
      <SectionHeader
        title="Profile details"
        description="Edit display metadata, locale, and timezone preferences."
      />
      <Form {...form}>
        <form className="space-y-4" onSubmit={onSubmit} noValidate>
          <div className="grid gap-4 md:grid-cols-2">
            <FormField
              control={form.control}
              name="displayName"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Display name</FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      placeholder="Ada Lovelace"
                      autoComplete="name"
                      maxLength={PROFILE_FIELD_LIMITS.displayName}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="avatarUrl"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Avatar URL</FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      type="url"
                      placeholder="https://"
                      autoComplete="url"
                      maxLength={PROFILE_FIELD_LIMITS.avatarUrl}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <FormField
              control={form.control}
              name="givenName"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Given name</FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      placeholder="Ada"
                      autoComplete="given-name"
                      maxLength={PROFILE_FIELD_LIMITS.givenName}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="familyName"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Family name</FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      placeholder="Lovelace"
                      autoComplete="family-name"
                      maxLength={PROFILE_FIELD_LIMITS.familyName}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <FormField
              control={form.control}
              name="timezone"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Timezone</FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      placeholder="America/Chicago"
                      maxLength={PROFILE_FIELD_LIMITS.timezone}
                    />
                  </FormControl>
                  <FormDescription>Suggested: {suggestedTimezone}</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="locale"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Locale</FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      placeholder="en-US"
                      maxLength={PROFILE_FIELD_LIMITS.locale}
                    />
                  </FormControl>
                  <FormDescription>Suggested: {suggestedLocale}</FormDescription>
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
            <p className="text-xs text-foreground/60">
              Leave fields blank to clear optional values. Updates apply immediately.
            </p>
            <Button className="md:w-auto" type="submit" disabled={isSaving || !form.formState.isDirty || !profile}>
              {isSaving ? 'Saving...' : 'Save profile'}
            </Button>
          </div>
        </form>
      </Form>
    </GlassPanel>
  );
}
