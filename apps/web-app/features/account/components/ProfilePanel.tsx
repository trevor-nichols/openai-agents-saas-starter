'use client';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { SectionHeader } from '@/components/ui/foundation';
import { ErrorState, SkeletonPanel } from '@/components/ui/states';
import { useToast } from '@/components/ui/use-toast';
import { useAccountProfileQuery, useResendVerificationMutation } from '@/lib/queries/account';
import { useCurrentUserProfileQuery } from '@/lib/queries/users';

import { AccountDisableCard } from './AccountDisableCard';
import { EmailChangeCard } from './EmailChangeCard';
import { ProfileDetailsCard } from './ProfileDetailsCard';
import { ProfileIdentityCard } from './ProfileIdentityCard';
import { ProfileQuickActionsCard } from './ProfileQuickActionsCard';
import { TenantSnapshotCard } from './TenantSnapshotCard';

export function ProfilePanel() {
  const {
    profile: accountProfile,
    tenantError,
    isLoadingProfile: isLoadingAccount,
    profileError: accountError,
    refetchProfile: refetchAccount,
  } = useAccountProfileQuery();
  const {
    profile: userProfile,
    isLoadingProfile: isLoadingUser,
    profileError: userError,
    refetchProfile: refetchUser,
  } = useCurrentUserProfileQuery();
  const resendVerification = useResendVerificationMutation();
  const toast = useToast();

  const combinedError = accountError ?? userError;
  const hasProfiles = Boolean(accountProfile && userProfile);
  const isLoading = (isLoadingAccount || isLoadingUser) && !hasProfiles;

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

  if (combinedError && !hasProfiles) {
    return (
      <section className="space-y-6">
        <SectionHeader
          eyebrow="Account"
          title="Profile"
          description="Display user metadata, tenant context, and verification state."
        />
        <ErrorState
          title="Unable to load profile"
          message={combinedError.message}
          onRetry={() => {
            refetchAccount();
            refetchUser();
          }}
        />
      </section>
    );
  }

  if (isLoading) {
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

  if (!accountProfile || !userProfile) {
    return null;
  }

  const emailVerified = userProfile.email_verified ?? accountProfile.verification.emailVerified;
  const showVerificationAlert = !emailVerified;
  const displayEmail = userProfile.email ?? accountProfile.user.email ?? 'your email';

  return (
    <section className="space-y-8">
      <SectionHeader
        eyebrow="Account"
        title="Profile"
        description="Confirm who’s signed in, update profile details, and manage verification."
      />

      {showVerificationAlert ? (
        <Alert variant="destructive" className="border border-warning/40 bg-warning/10 text-warning">
          <AlertTitle>Email verification required</AlertTitle>
          <AlertDescription className="mt-2 flex flex-wrap items-center gap-3">
            We sent a verification link to{' '}
            <span className="font-semibold text-warning-foreground">{displayEmail}</span>. Finish verification
            to unlock billing and export actions.
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
        <ProfileIdentityCard profile={userProfile} />
        <ProfileDetailsCard profile={userProfile} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <EmailChangeCard profile={userProfile} />
        <TenantSnapshotCard
          tenant={accountProfile.tenant}
          tenantError={tenantError}
          userRole={userProfile.role ?? accountProfile.user.role}
          onRetry={() => refetchAccount()}
        />
      </div>

      <AccountDisableCard />

      <ProfileQuickActionsCard sessionExpiresAt={accountProfile.session.expiresAt} />
    </section>
  );
}
