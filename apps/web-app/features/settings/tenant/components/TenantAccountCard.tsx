'use client';

import { useMemo, useState } from 'react';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { GlassPanel, InlineTag, KeyValueList, SectionHeader } from '@/components/ui/foundation';
import { Input } from '@/components/ui/input';
import { SkeletonPanel } from '@/components/ui/states';
import { useToast } from '@/components/ui/use-toast';
import { formatDateTime } from '@/lib/utils/time';
import type { TenantAccount, TenantAccountSelfUpdateInput } from '@/types/tenantAccount';

interface TenantAccountCardProps {
  account: TenantAccount | null;
  isLoading: boolean;
  error: Error | null;
  isSaving: boolean;
  onRetry: () => void;
  onSubmit: (payload: TenantAccountSelfUpdateInput) => Promise<unknown>;
}

const statusLabel: Record<string, string> = {
  provisioning: 'Provisioning',
  active: 'Active',
  suspended: 'Suspended',
  deprovisioning: 'Deprovisioning',
  deprovisioned: 'Deprovisioned',
};

const statusTone: Record<string, 'default' | 'positive' | 'warning'> = {
  provisioning: 'warning',
  active: 'positive',
  suspended: 'warning',
  deprovisioning: 'warning',
  deprovisioned: 'default',
};

export function TenantAccountCard({
  account,
  isLoading,
  error,
  isSaving,
  onRetry,
  onSubmit,
}: TenantAccountCardProps) {
  const toast = useToast();
  const [draftName, setDraftName] = useState<string | null>(null);
  const resolvedName = draftName ?? account?.name ?? '';

  const hasChanges = useMemo(() => {
    if (!account) return false;
    return resolvedName.trim() !== account.name;
  }, [resolvedName, account]);

  const handleSave = async () => {
    const trimmed = resolvedName.trim();
    if (!trimmed) {
      toast.error({
        title: 'Name is required',
        description: 'Provide a tenant name before saving.',
      });
      return;
    }
    try {
      await onSubmit({ name: trimmed });
      setDraftName(null);
      toast.success({
        title: 'Tenant account updated',
        description: 'The tenant name was saved successfully.',
      });
    } catch (err) {
      toast.error({
        title: 'Unable to update tenant account',
        description: err instanceof Error ? err.message : 'Try again shortly.',
      });
    }
  };

  const metadataItems = account
    ? [
        { label: 'Slug', value: account.slug },
        {
          label: 'Status',
      value: (
            <InlineTag tone={statusTone[account.status] ?? 'default'}>
              {statusLabel[account.status] ?? account.status}
            </InlineTag>
          ),
        },
        { label: 'Created', value: formatDateTime(account.createdAt) },
        { label: 'Updated', value: formatDateTime(account.updatedAt) },
        ...(account.suspendedAt
          ? [{ label: 'Suspended', value: formatDateTime(account.suspendedAt) }]
          : []),
        ...(account.deprovisionedAt
          ? [{ label: 'Deprovisioned', value: formatDateTime(account.deprovisionedAt) }]
          : []),
      ]
    : [];

  return (
    <GlassPanel className="space-y-6">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <SectionHeader
          eyebrow="Tenant account"
          title="Tenant profile"
          description="Update the tenant name and review lifecycle status."
        />
        <Button type="button" onClick={handleSave} disabled={!hasChanges || isSaving || !account}>
          {isSaving ? 'Saving…' : 'Save changes'}
        </Button>
      </div>

      {isLoading ? (
        <SkeletonPanel lines={4} />
      ) : error ? (
        <Alert variant="destructive">
          <AlertTitle>Tenant account unavailable</AlertTitle>
          <AlertDescription className="mt-2 flex flex-col gap-2">
            <span>{error.message}</span>
            <Button size="sm" variant="outline" onClick={onRetry}>
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      ) : account ? (
        <div className="space-y-4">
          {account.status !== 'active' ? (
            <Alert variant="destructive" className="border-warning/40 bg-warning/5 text-foreground">
              <AlertTitle>Tenant lifecycle notice</AlertTitle>
              <AlertDescription>
                This tenant is currently {statusLabel[account.status] ?? account.status}. Some operations may be
                limited until the tenant is active again.
              </AlertDescription>
            </Alert>
          ) : null}

          <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
            <div className="space-y-2">
              <label className="text-xs uppercase tracking-[0.2em] text-foreground/50">Tenant name</label>
              <Input
                value={resolvedName}
                onChange={(event) => setDraftName(event.target.value)}
                placeholder="Tenant name"
              />
              <p className="text-xs text-foreground/60">
                Tenant admins can update the name; the slug remains operator-only.
              </p>
            </div>
            <KeyValueList items={metadataItems} columns={1} />
          </div>
        </div>
      ) : (
        <p className="text-sm text-foreground/60">Tenant account details are unavailable.</p>
      )}
    </GlassPanel>
  );
}
