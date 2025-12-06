'use client';

import { useMemo } from 'react';

import { SectionHeader } from '@/components/ui/foundation';
import { ErrorState, SkeletonPanel } from '@/components/ui/states';
import { useAccountProfileQuery } from '@/lib/queries/account';

import { AdminResetGate } from '../security/components/AdminResetGate';
import { MfaPreviewCard } from '../security/components/MfaPreviewCard';
import { PasswordChangeCard } from '../security/components/PasswordChangeCard';
import { RecentActivityCard } from '../security/components/RecentActivityCard';
import { SUPPORT_SCOPE } from '../security/constants';
import { usePasswordChangeForm } from '../security/hooks/usePasswordChangeForm';
import { extractDateField } from '../utils/dates';
import type { AccountProfileTokenPayload } from '@/types/account';

export function SecurityPanel() {
  const { profile, isLoadingProfile, profileError, refetchProfile } = useAccountProfileQuery();
  const { form, onSubmit, isSaving, rootError } = usePasswordChangeForm();

  const tokenPayload = useMemo(() => {
    if (!profile) return null;
    const payload = profile.raw.session?.profile?.token_payload;
    return (payload ?? null) as AccountProfileTokenPayload | null;
  }, [profile]);

  const hasSupportScope = useMemo(
    () => profile?.session.scopes?.includes(SUPPORT_SCOPE) ?? false,
    [profile?.session.scopes],
  );
  const hasTenantContext = Boolean(profile?.tenant?.id);

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
        <PasswordChangeCard form={form} onSubmit={onSubmit} isSaving={isSaving} rootError={rootError} />
        <MfaPreviewCard />
      </div>

      <AdminResetGate
        hasSupportScope={hasSupportScope}
        hasTenantContext={hasTenantContext}
        tenantName={profile.tenant?.name ?? null}
      />

      <RecentActivityCard
        isLoading={isLoadingProfile}
        hasData={Boolean(profile)}
        lastLoginAt={lastLoginAt}
        passwordChangedAt={passwordChangedAt}
        sessionExpiresAt={profile.session.expiresAt}
        emailVerified={profile.verification.emailVerified}
      />
    </section>
  );
}
