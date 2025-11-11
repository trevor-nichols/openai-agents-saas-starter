'use client';

import Link from 'next/link';
import { useMemo } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';

import { useAccountProfileQuery } from '@/lib/queries/account';
import { useChangePasswordMutation } from '@/lib/queries/accountSecurity';
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
import { GlassPanel, InlineTag, KeyValueList, SectionHeader } from '@/components/ui/foundation';
import { Input } from '@/components/ui/input';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { useToast } from '@/components/ui/use-toast';
import type { AccountProfileTokenPayload } from '@/types/account';

const passwordSchema = z
  .object({
    currentPassword: z.string().min(1, 'Enter your current password.'),
    newPassword: z.string().min(14, 'New password must be at least 14 characters.'),
    confirmNewPassword: z.string().min(1, 'Confirm your new password.'),
  })
  .refine((values) => values.newPassword === values.confirmNewPassword, {
    path: ['confirmNewPassword'],
    message: 'Passwords must match.',
  });

type PasswordFormValues = z.infer<typeof passwordSchema>;

const MFA_DOC_URL = 'https://github.com/openai/openai-agents-starter/blob/main/docs/security/mfa-roadmap.md';

export function SecurityPanel() {
  const { profile, isLoadingProfile, profileError, refetchProfile } = useAccountProfileQuery();
  const toast = useToast();
  const changePassword = useChangePasswordMutation();

  const form = useForm<PasswordFormValues>({
    resolver: zodResolver(passwordSchema),
    defaultValues: {
      currentPassword: '',
      newPassword: '',
      confirmNewPassword: '',
    },
  });

  const handleSubmit = form.handleSubmit(async (values) => {
    form.clearErrors('root');
    try {
      await changePassword.mutateAsync({
        current_password: values.currentPassword,
        new_password: values.newPassword,
      });
      toast.success({
        title: 'Password updated',
        description: 'All other sessions were signed out.',
      });
      form.reset();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Double-check your credentials and try again.';
      form.setError('root', { message });
      toast.error({
        title: 'Unable to change password',
        description: message,
      });
    }
  });

  const tokenPayload = useMemo(() => {
    if (!profile) return null;
    const payload = profile.raw.session?.profile?.token_payload;
    return (payload ?? null) as AccountProfileTokenPayload | null;
  }, [profile]);

  const lastLoginAt = extractDateField(tokenPayload, ['last_login_at', 'last_login']);
  const passwordChangedAt = extractDateField(tokenPayload, ['password_changed_at']);

  if (profileError && !profile) {
    return (
      <section className="space-y-6">
        <SectionHeader
          eyebrow="Account"
          title="Security"
          description="Manage passwords, MFA, and recent session activity."
        />
        <ErrorState title="Unable to load security data" message={profileError.message} onRetry={() => refetchProfile()} />
      </section>
    );
  }

  if (isLoadingProfile && !profile) {
    return (
      <section className="space-y-6">
        <SectionHeader
          eyebrow="Account"
          title="Security"
          description="Manage passwords, MFA, and recent session activity."
        />
        <div className="grid gap-6 lg:grid-cols-2">
          <SkeletonPanel lines={6} />
          <SkeletonPanel lines={6} />
        </div>
        <SkeletonPanel lines={4} />
      </section>
    );
  }

  if (!profile) {
    return null;
  }

  return (
    <section className="space-y-8">
      <SectionHeader
        eyebrow="Account"
        title="Security"
        description="Rotate your password, preview MFA, and keep tabs on recent access."
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <GlassPanel className="space-y-6">
          <SectionHeader
            title="Password & sign-in"
            description="Update your password. We’ll sign out other sessions automatically."
          />
          <Form {...form}>
            <form className="space-y-4" onSubmit={handleSubmit} noValidate>
              <FormField
                control={form.control}
                name="currentPassword"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Current password</FormLabel>
                    <FormControl>
                      <Input {...field} type="password" autoComplete="current-password" />
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

              {form.formState.errors.root ? (
                <p className="text-sm font-medium text-destructive" role="alert">
                  {form.formState.errors.root.message}
                </p>
              ) : null}

              <Button className="w-full" type="submit" disabled={changePassword.isPending}>
                {changePassword.isPending ? 'Saving...' : 'Update password'}
              </Button>
            </form>
          </Form>

          <div className="rounded-lg border border-white/10 bg-white/5 p-4 text-sm text-foreground/70">
            <p className="font-medium text-foreground">Password requirements</p>
            <ul className="mt-2 list-disc space-y-1 pl-5">
              <li>14+ characters with upper, lower, number, and symbol.</li>
              <li>No reuse of the last 5 passwords.</li>
              <li>Strength score ≥3 on our policy engine.</li>
            </ul>
          </div>
        </GlassPanel>

        <GlassPanel className="space-y-6">
          <SectionHeader
            title="Multi-factor authentication"
            description="Passkeys + TOTP enrollment ship alongside the enterprise security milestone."
            actions={<InlineTag tone="warning">Planned</InlineTag>}
          />
          <p className="text-sm text-foreground/70">
            MFA will support passkeys (WebAuthn) and backup TOTP codes so operators can secure both the dashboard
            and CLI flows. Admins will be able to enforce tenant-wide MFA once rollout completes.
          </p>
          <div className="flex flex-wrap gap-3">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="secondary" disabled>
                    Enable MFA
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="top">Coming soon—follow the roadmap for updates.</TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <Button asChild variant="outline">
              <Link href={MFA_DOC_URL} target="_blank" rel="noreferrer">
                View MFA roadmap
              </Link>
            </Button>
          </div>
          <Alert className="border border-warning/40 bg-warning/10 text-warning">
            <AlertTitle>Heads up</AlertTitle>
            <AlertDescription>
              Until MFA ships, make sure every admin uses a password manager and rotates credentials quarterly.
            </AlertDescription>
          </Alert>
        </GlassPanel>
      </div>

      <GlassPanel className="space-y-6">
        <SectionHeader
          title="Recent activity"
          description="Quick snapshot of the current session. Visit Sessions for full device history."
        />

        {isLoadingProfile ? (
          <SkeletonPanel lines={3} className="bg-transparent p-0" />
        ) : profile ? (
          <>
            <KeyValueList
              columns={2}
              items={[
                { label: 'Last login', value: formatDateTime(lastLoginAt) },
                { label: 'Session expires', value: formatDateTime(profile.session.expiresAt) },
                { label: 'Password updated', value: formatDateTime(passwordChangedAt) },
                { label: 'Email status', value: profile.verification.emailVerified ? 'Verified' : 'Verification pending' },
              ]}
            />
            <div className="flex flex-wrap gap-3">
              <Button asChild variant="secondary">
                <Link href="/account/sessions">View sessions</Link>
              </Button>
              <Button asChild variant="outline">
                <Link href="/account/service-accounts">Manage service accounts</Link>
              </Button>
            </div>
          </>
        ) : (
          <EmptyState
            title="Session unavailable"
            description="We couldn’t load session metadata for this user. Refresh and try again."
          />
        )}
      </GlassPanel>
    </section>
  );
}

function extractDateField(payload: AccountProfileTokenPayload | null, keys: string[]): string | null {
  if (!payload) return null;
  for (const key of keys) {
    const value = payload[key];
    if (typeof value === 'string') {
      return value;
    }
  }
  return null;
}

function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return '—';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '—';
  }
  return date.toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}
