'use client';

import Link from 'next/link';
import { useMemo } from 'react';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { GlassPanel, InlineTag, KeyValueList, SectionHeader } from '@/components/ui/foundation';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import { useToast } from '@/components/ui/use-toast';
import { useAccountProfileQuery, useResendVerificationMutation } from '@/lib/queries/account';
import { formatDateTime } from '../utils/dates';

export function ProfilePanel() {
  const { profile, tenantError, isLoadingProfile, profileError, refetchProfile } =
    useAccountProfileQuery();
  const resendVerification = useResendVerificationMutation();
  const toast = useToast();

  const initials = useMemo(() => {
    if (!profile) {
      return 'AA';
    }
    const source = profile.user.displayName || profile.user.email || '';
    return source
      .split(' ')
      .filter(Boolean)
      .map((chunk) => chunk[0]?.toUpperCase())
      .slice(0, 2)
      .join('');
  }, [profile]);

  const handleResendVerification = async () => {
    try {
      await resendVerification.mutateAsync();
      toast.success({
        title: 'Verification email sent',
        description: 'Check your inbox for the confirmation link.',
      });
    } catch (error) {
      toast.error({
        title: 'Unable to send verification email',
        description: error instanceof Error ? error.message : 'Please try again shortly.',
      });
    }
  };

  if (profileError) {
    return (
      <section className="space-y-6">
        <SectionHeader
          eyebrow="Account"
          title="Profile"
          description="Display user metadata, tenant context, and verification state."
        />
        <ErrorState
          title="Unable to load profile"
          message={profileError.message}
          onRetry={() => refetchProfile()}
        />
      </section>
    );
  }

  if (isLoadingProfile && !profile) {
    return (
      <section className="space-y-6">
        <SectionHeader
          eyebrow="Account"
          title="Profile"
          description="Display user metadata, tenant context, and verification state."
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

  const showVerificationAlert = !profile.verification.emailVerified;
  const tenant = profile.tenant;

  return (
    <section className="space-y-8">
      <SectionHeader
        eyebrow="Account"
        title="Profile"
        description="Confirm who’s signed in, see tenant metadata, and manage verification."
      />

      {showVerificationAlert ? (
        <Alert variant="destructive" className="border border-warning/40 bg-warning/10 text-warning">
          <AlertTitle>Email verification required</AlertTitle>
          <AlertDescription className="mt-2 flex flex-wrap items-center gap-3">
            We sent a verification link to{' '}
            <span className="font-semibold text-warning-foreground">{profile.user.email}</span>.
            Finish verification to unlock billing and export actions.
            <Button
              size="sm"
              variant="secondary"
              disabled={resendVerification.isPending}
              onClick={handleResendVerification}
            >
              {resendVerification.isPending ? 'Sending...' : 'Resend verification'}
            </Button>
          </AlertDescription>
        </Alert>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <GlassPanel className="space-y-6">
          <SectionHeader
            title="Identity"
            description="Profile metadata for this signed-in human."
            actions={
              <InlineTag tone={profile.verification.emailVerified ? 'positive' : 'warning'}>
                {profile.verification.emailVerified ? 'Email verified' : 'Verification pending'}
              </InlineTag>
            }
          />
          <div className="flex flex-wrap items-center gap-4">
            <Avatar className="h-16 w-16 border border-white/10">
              <AvatarImage src={profile.user.avatarUrl ?? undefined} alt={profile.user.displayName ?? ''} />
              <AvatarFallback>{initials || 'AA'}</AvatarFallback>
            </Avatar>
            <div className="space-y-1">
              <p className="text-lg font-semibold text-foreground">
                {profile.user.displayName ?? 'Unnamed user'}
              </p>
              <p className="text-sm text-foreground/70">{profile.user.email ?? 'No email on file'}</p>
              <p className="text-xs uppercase tracking-[0.3em] text-foreground/50">
                {profile.user.role ?? 'member'}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button
              variant="secondary"
              disabled={!showVerificationAlert || resendVerification.isPending}
              onClick={handleResendVerification}
            >
              {resendVerification.isPending ? 'Sending...' : 'Resend verification'}
            </Button>
            <Button variant="outline" disabled>
              Edit profile (coming soon)
            </Button>
          </div>
        </GlassPanel>

        <GlassPanel className="space-y-6">
          <SectionHeader
            title="Tenant snapshot"
            description="Plan and seat metadata for your current workspace."
            actions={
              tenant?.planCode ? (
                <InlineTag tone="default">{tenant.planCode}</InlineTag>
              ) : null
            }
          />

          {tenant ? (
            <>
              <KeyValueList
                columns={2}
                items={[
                  { label: 'Tenant', value: tenant.name ?? 'Unknown', hint: tenant.slug ? `Slug · ${tenant.slug}` : undefined },
                  { label: 'Role', value: profile.user.role ?? 'member' },
                  { label: 'Seats', value: tenant.seatCount ?? '—' },
                  { label: 'Auto renew', value: tenant.autoRenew ? 'Enabled' : 'Disabled' },
                  {
                    label: 'Current period',
                    value:
                      tenant.currentPeriodStart && tenant.currentPeriodEnd
                        ? `${formatDateTime(tenant.currentPeriodStart)} → ${formatDateTime(tenant.currentPeriodEnd)}`
                        : '—',
                  },
                  {
                    label: 'Billing contact',
                    value: tenant.billingEmail ?? 'Not set',
                  },
                ]}
              />
              <div className="flex flex-wrap gap-3">
                <Button asChild variant="secondary">
                  <Link href="/billing">Open billing</Link>
                </Button>
                <Button asChild variant="outline">
                  <Link href="/account?tab=automation">Service accounts</Link>
                </Button>
              </div>
            </>
          ) : tenantError ? (
            <Alert variant="destructive">
              <AlertTitle>Tenant details unavailable</AlertTitle>
              <AlertDescription className="mt-2 space-y-2">
                {tenantError.message}
                <Button size="sm" onClick={() => refetchProfile()}>
                  Retry
                </Button>
              </AlertDescription>
            </Alert>
          ) : (
            <EmptyState
              title="Tenant context missing"
              description="Sign in again to reload tenant metadata."
            />
          )}
        </GlassPanel>
      </div>

      <GlassPanel className="space-y-4">
        <SectionHeader
          title="Metadata & quick actions"
          description="Jump into deeper account tools as needed."
        />
        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-foreground/50">Recent activity</p>
            <div className="mt-2 space-y-2 text-sm text-foreground/80">
              <div className="flex justify-between">
                <span>Last login</span>
                <span className="text-right text-foreground/60">See Sessions</span>
              </div>
              <div className="flex justify-between">
                <span>Session expires</span>
                <span className="text-right">{formatDateTime(profile.session.expiresAt)}</span>
              </div>
            </div>
            <Button asChild variant="outline" size="sm" className="mt-3 w-full">
              <Link href="/account?tab=sessions">View sessions</Link>
            </Button>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-foreground/50">Service accounts</p>
            <p className="mt-2 text-sm text-foreground/70">
              Issue or revoke automation tokens from the Automation tab.
            </p>
            <div className="mt-3 flex flex-col gap-2">
              <Button asChild variant="secondary" size="sm">
                <Link href="/account?tab=automation">Open automation</Link>
              </Button>
              <Button asChild variant="outline" size="sm">
                <Link href="/docs/frontend/features/account-service-accounts.md">CLI guide</Link>
              </Button>
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-foreground/50">Billing</p>
            <p className="mt-2 text-sm text-foreground/70">
              Update plan, seats, and payment details from Billing.
            </p>
            <div className="mt-3 flex flex-col gap-2">
              <Button asChild variant="secondary" size="sm">
                <Link href="/billing">Open billing</Link>
              </Button>
              <Button asChild variant="outline" size="sm">
                <Link href="/settings/tenant">Tenant settings</Link>
              </Button>
            </div>
          </div>
        </div>
      </GlassPanel>
    </section>
  );
}
