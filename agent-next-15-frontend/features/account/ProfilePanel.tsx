'use client';

import Link from 'next/link';
import { useMemo } from 'react';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { GlassPanel, InlineTag, KeyValueList, SectionHeader } from '@/components/ui/foundation';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { useToast } from '@/components/ui/use-toast';
import { useAccountProfileQuery, useResendVerificationMutation } from '@/lib/queries/account';

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

  const formatDateTime = (value: string | null | undefined) => {
    if (!value) return '—';
    return new Date(value).toLocaleString(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    });
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
            <TooltipProvider delayDuration={200}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="outline" disabled>
                    Edit profile
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="top">Coming soon</TooltipContent>
              </Tooltip>
            </TooltipProvider>
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
        <Accordion type="multiple" className="w-full space-y-2">
          <AccordionItem value="activity">
            <AccordionTrigger className="text-left text-sm font-semibold uppercase tracking-[0.3em] text-foreground/60">
              Recent activity
            </AccordionTrigger>
            <AccordionContent>
              <KeyValueList
                items={[
                  {
                    label: 'Last login',
                    value: 'See Sessions for full device history',
                  },
                  {
                    label: 'Session expires',
                    value: formatDateTime(profile.session.expiresAt),
                  },
                ]}
              />
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="service-accounts">
            <AccordionTrigger className="text-left text-sm font-semibold uppercase tracking-[0.3em] text-foreground/60">
              Service accounts
            </AccordionTrigger>
            <AccordionContent className="space-y-3">
              <p className="text-sm text-foreground/70">
                Audit and revoke automation tokens from the Automation tab. Issuing new credentials still flows through
                the Starter CLI until Vault-backed self-serve flows launch.
              </p>
              <div className="flex flex-wrap gap-2">
                <Button asChild variant="secondary">
                  <Link href="/account?tab=automation">Open automation tab</Link>
                </Button>
                <Button asChild variant="outline">
                  <Link href="/docs/frontend/features/account-service-accounts.md">CLI guide</Link>
                </Button>
              </div>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="sessions">
            <AccordionTrigger className="text-left text-sm font-semibold uppercase tracking-[0.3em] text-foreground/60">
              Session management
            </AccordionTrigger>
            <AccordionContent className="space-y-3">
              <p className="text-sm text-foreground/70">
                Review active devices, revoke stale sessions, and audit login activity.
              </p>
              <Button asChild variant="outline">
                <Link href="/account?tab=sessions">View sessions</Link>
              </Button>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </GlassPanel>
    </section>
  );
}
