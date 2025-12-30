'use client';

import Link from 'next/link';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { GlassPanel, InlineTag, KeyValueList, SectionHeader } from '@/components/ui/foundation';
import { EmptyState } from '@/components/ui/states';
import type { AccountTenantSummary } from '@/types/account';
import type { TeamRole } from '@/types/team';
import { formatDateTime } from '../utils/dates';

interface TenantSnapshotCardProps {
  tenant: AccountTenantSummary | null;
  tenantError: Error | null;
  userRole: TeamRole | null;
  onRetry: () => void;
}

export function TenantSnapshotCard({ tenant, tenantError, userRole, onRetry }: TenantSnapshotCardProps) {
  return (
    <GlassPanel className="space-y-6">
      <SectionHeader
        title="Tenant snapshot"
        description="Plan and seat metadata for your current workspace."
        actions={tenant?.planCode ? <InlineTag tone="default">{tenant.planCode}</InlineTag> : null}
      />

      {tenant ? (
        <>
          <KeyValueList
            columns={2}
            items={[
              { label: 'Tenant', value: tenant.name ?? 'Unknown', hint: tenant.slug ? `Slug · ${tenant.slug}` : undefined },
              { label: 'Role', value: userRole ?? 'member' },
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
            <Button size="sm" onClick={onRetry}>
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
  );
}
