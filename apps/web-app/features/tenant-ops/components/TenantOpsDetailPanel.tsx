'use client';

import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import { GlassPanel, InlineTag, KeyValueList, SectionHeader } from '@/components/ui/foundation';
import { Separator } from '@/components/ui/separator';
import { formatDateTime } from '@/lib/utils/time';
import type { TenantAccountOperatorSummary } from '@/types/tenantAccount';

import { TENANT_STATUS_LABELS, TENANT_STATUS_TONES } from '../constants';
import type { TenantLifecycleAction } from '../types';
import { resolveLifecycleActions } from '../utils';

type DetailPanelVariant = 'panel' | 'plain';

interface TenantOpsDetailPanelProps {
  tenant: TenantAccountOperatorSummary | null;
  isLoading: boolean;
  error: Error | null;
  onRetry: () => void;
  onEdit: () => void;
  onCreate: () => void;
  onAction: (action: TenantLifecycleAction) => void;
  isBusy?: boolean;
  variant?: DetailPanelVariant;
}

export function TenantOpsDetailPanel({
  tenant,
  isLoading,
  error,
  onRetry,
  onEdit,
  onCreate,
  onAction,
  isBusy = false,
  variant = 'panel',
}: TenantOpsDetailPanelProps) {
  const actions = tenant ? resolveLifecycleActions(tenant.status) : [];
  const Container = variant === 'panel' ? GlassPanel : 'div';

  const statusLabel = tenant ? TENANT_STATUS_LABELS[tenant.status] ?? tenant.status : '—';
  const statusTone = tenant ? TENANT_STATUS_TONES[tenant.status] ?? 'default' : 'default';

  const metadataItems = tenant
    ? [
        { label: 'Slug', value: tenant.slug },
        { label: 'Status', value: <InlineTag tone={statusTone}>{statusLabel}</InlineTag> },
        { label: 'Status updated', value: formatDateTime(tenant.statusUpdatedAt) },
        { label: 'Status reason', value: tenant.statusReason ?? '—' },
        { label: 'Updated by', value: tenant.statusUpdatedBy ?? '—' },
        { label: 'Created', value: formatDateTime(tenant.createdAt) },
        { label: 'Updated', value: formatDateTime(tenant.updatedAt) },
        { label: 'Suspended', value: formatDateTime(tenant.suspendedAt) },
        { label: 'Deprovisioned', value: formatDateTime(tenant.deprovisionedAt) },
      ]
    : [];

  if (!tenant) {
    return (
      <Container className={variant === 'panel' ? 'space-y-6' : 'space-y-6'}>
        {isLoading ? (
          <SkeletonPanel lines={6} />
        ) : error ? (
          <ErrorState
            title="Unable to load tenant"
            message={error.message}
            onRetry={onRetry}
          />
        ) : (
          <EmptyState
            title="Select a tenant"
            description="Choose a tenant from the list to review status or apply lifecycle actions."
            action={(
              <Button onClick={onCreate}>
                Create tenant
              </Button>
            )}
          />
        )}
      </Container>
    );
  }

  return (
    <Container className={variant === 'panel' ? 'space-y-6' : 'space-y-6'}>
      <div className="space-y-6">
        <SectionHeader
          eyebrow="Tenant detail"
          title={tenant.name}
          description="Review identity, lifecycle status, and audit details."
          size="compact"
          actions={(
            <Button variant="outline" onClick={onEdit} disabled={isBusy}>
              Edit details
            </Button>
          )}
        />

        {error ? (
          <Alert className="border-warning/40 bg-warning/5 text-foreground">
            <AlertTitle>Detail data unavailable</AlertTitle>
            <AlertDescription className="mt-2 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <span>{error.message}</span>
              <Button size="sm" variant="outline" onClick={onRetry}>
                Retry
              </Button>
            </AlertDescription>
          </Alert>
        ) : null}

        <KeyValueList items={metadataItems} columns={1} />

        <Separator className="bg-white/10" />

        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-foreground">Lifecycle actions</h3>
          <div className="flex flex-wrap gap-2">
            {actions.length === 0 ? (
              <p className="text-sm text-foreground/60">No lifecycle actions available for this tenant.</p>
            ) : (
              actions.map((action) => (
                <Button
                  key={action}
                  variant={action === 'deprovision' ? 'destructive' : 'outline'}
                  disabled={isBusy}
                  onClick={() => onAction(action)}
                >
                  {action === 'suspend' && 'Suspend'}
                  {action === 'reactivate' && 'Reactivate'}
                  {action === 'deprovision' && 'Deprovision'}
                </Button>
              ))
            )}
          </div>
          <p className="text-xs text-foreground/60">
            Lifecycle actions require an audit reason and are logged for compliance.
          </p>
        </div>
      </div>
    </Container>
  );
}
