'use client';

import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { GlassPanel, KeyValueList, SectionHeader } from '@/components/ui/foundation';
import { EmptyState, SkeletonPanel } from '@/components/ui/states';
import { formatDateTime } from '../../utils/dates';

interface RecentActivityCardProps {
  isLoading: boolean;
  hasData: boolean;
  lastLoginAt: string | null;
  passwordChangedAt: string | null;
  sessionExpiresAt: string | null;
  emailVerified: boolean;
}

export function RecentActivityCard({
  isLoading,
  hasData,
  lastLoginAt,
  passwordChangedAt,
  sessionExpiresAt,
  emailVerified,
}: RecentActivityCardProps) {
  return (
    <GlassPanel className="space-y-6">
      <SectionHeader
        title="Recent activity"
        description="Quick snapshot of the current session. Visit Sessions for full device history."
      />

      {isLoading ? (
        <SkeletonPanel lines={3} className="bg-transparent p-0" />
      ) : hasData ? (
        <>
          <KeyValueList
            columns={2}
            items={[
              { label: 'Last login', value: formatDateTime(lastLoginAt) },
              { label: 'Session expires', value: formatDateTime(sessionExpiresAt) },
              { label: 'Password updated', value: formatDateTime(passwordChangedAt) },
              { label: 'Email status', value: emailVerified ? 'Verified' : 'Verification pending' },
            ]}
          />
          <div className="flex flex-wrap gap-3">
            <Button asChild variant="secondary">
              <Link href="/account?tab=sessions">View sessions</Link>
            </Button>
            <Button asChild variant="outline">
              <Link href="/account?tab=automation">Service-account guidance</Link>
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
  );
}
