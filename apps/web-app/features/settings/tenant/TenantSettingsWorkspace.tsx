'use client';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { GlassPanel, SectionHeader } from '@/components/ui/foundation';
import { SkeletonPanel, ErrorState } from '@/components/ui/states';
import { TenantSettingsApiError } from '@/lib/api/tenantSettings';
import { useTenantAccountQuery, useUpdateTenantAccountMutation } from '@/lib/queries/tenantAccount';
import { useTenantSettingsQuery, useUpdateTenantSettingsMutation } from '@/lib/queries/tenantSettings';
import type { BillingContact } from '@/types/tenantSettings';

import { BillingContactsCard, PlanMetadataCard, TenantAccountCard, TenantFlagsCard, WebhookSettingsCard } from './components';

interface TenantSettingsWorkspaceProps {
  canManageBilling: boolean;
  canManageTenantSettings: boolean;
  canManageTenantAccount: boolean;
}

export function TenantSettingsWorkspace({
  canManageBilling,
  canManageTenantSettings,
  canManageTenantAccount,
}: TenantSettingsWorkspaceProps) {
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useTenantSettingsQuery({ enabled: canManageTenantSettings });
  const updateMutation = useUpdateTenantSettingsMutation();
  const accountQuery = useTenantAccountQuery({ enabled: canManageTenantAccount });
  const accountMutation = useUpdateTenantAccountMutation();

  if (!canManageTenantSettings) {
    return (
      <section className="space-y-6">
        <SectionHeader
          eyebrow="Settings"
          title="Tenant settings"
          description="Manage billing contacts, webhooks, plan metadata, and feature toggles."
        />
        <GlassPanel className="space-y-2 border border-warning/40 bg-warning/5">
          <p className="text-base font-semibold text-foreground">Tenant settings access restricted</p>
          <p className="text-sm text-foreground/70">
            You need tenant admin access to view settings. Ask an administrator to update your role or scopes,
            then refresh this page.
          </p>
        </GlassPanel>
      </section>
    );
  }

  const lastUpdated = data?.updatedAt
    ? new Intl.DateTimeFormat('en-US', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(data.updatedAt))
    : null;

  const isSavingSettings = updateMutation.isPending;
  const isSavingAccount = accountMutation.isPending;

  const handleContactsSave = async (contacts: BillingContact[]) => {
    await updateMutation.mutateAsync({ billingContacts: contacts });
  };

  const handleWebhookSave = async (url: string | null) => {
    await updateMutation.mutateAsync({ billingWebhookUrl: url });
  };

  const handleMetadataSave = async (metadata: Record<string, string>) => {
    await updateMutation.mutateAsync({ planMetadata: metadata });
  };

  const handleFlagsSave = async (flags: Record<string, boolean>) => {
    await updateMutation.mutateAsync({ flags });
  };

  const settingsError = error instanceof Error ? error : null;
  const isSettingsForbidden =
    settingsError instanceof TenantSettingsApiError && settingsError.status === 403;
  const showSettingsSkeleton = !data && isLoading;

  let settingsContent: React.ReactNode = null;
  if (showSettingsSkeleton) {
    settingsContent = (
      <div className="space-y-4">
        <SkeletonPanel lines={6} />
        <SkeletonPanel lines={4} />
        <SkeletonPanel lines={4} />
      </div>
    );
  } else if (isSettingsForbidden) {
    settingsContent = (
      <GlassPanel className="space-y-2 border border-warning/40 bg-warning/5">
        <p className="text-base font-semibold text-foreground">Tenant settings access restricted</p>
        <p className="text-sm text-foreground/70">
          Your current access level cannot view tenant settings. Ask an administrator to grant the
          required role or billing permissions, then refresh this page.
        </p>
      </GlassPanel>
    );
  } else if (settingsError) {
    settingsContent = (
      <ErrorState
        title="Unable to load tenant settings"
        message={settingsError.message}
        onRetry={() => refetch()}
      />
    );
  } else if (data) {
    settingsContent = (
      <>
        {!canManageBilling ? (
          <Alert className="border-warning/40 bg-warning/5 text-foreground">
            <AlertTitle>Billing access required</AlertTitle>
            <AlertDescription>
              Billing contacts, webhooks, and plan metadata are restricted to the <span className="font-semibold">billing:manage</span> scope.
              Ask an administrator to grant billing access if you need to update these settings.
            </AlertDescription>
          </Alert>
        ) : null}

        {canManageBilling ? (
          <>
            <BillingContactsCard
              contacts={data.billingContacts}
              isSaving={isSavingSettings}
              onSubmit={handleContactsSave}
            />
            <WebhookSettingsCard
              webhookUrl={data.billingWebhookUrl}
              isSaving={isSavingSettings}
              onSubmit={handleWebhookSave}
            />
            <PlanMetadataCard
              planMetadata={data.planMetadata}
              isSaving={isSavingSettings}
              onSubmit={handleMetadataSave}
            />
          </>
        ) : null}
        <TenantFlagsCard flags={data.flags} isSaving={isSavingSettings} onSubmit={handleFlagsSave} />
      </>
    );
  }

  return (
    <section className="space-y-8">
      <GlassPanel className="space-y-4">
        <SectionHeader
          eyebrow="Settings"
          title="Tenant controls"
          description="Give operators a single surface to manage billing contacts, automation hooks, and feature toggles."
        />
        {lastUpdated ? (
          <p className="text-sm text-foreground/60">Last updated {lastUpdated}</p>
        ) : null}
      </GlassPanel>

      <div className="space-y-6">
        {canManageTenantAccount ? (
          <TenantAccountCard
            key={accountQuery.data?.id ?? 'tenant-account'}
            account={accountQuery.data ?? null}
            isLoading={accountQuery.isLoading}
            error={(accountQuery.error as Error) ?? null}
            isSaving={isSavingAccount}
            onRetry={() => accountQuery.refetch()}
            onSubmit={(payload) => accountMutation.mutateAsync(payload)}
          />
        ) : (
          <GlassPanel className="space-y-2 border border-warning/40 bg-warning/5">
            <p className="text-base font-semibold text-foreground">Tenant account access restricted</p>
            <p className="text-sm text-foreground/70">
              Only <span className="font-semibold">owner</span> or <span className="font-semibold">admin</span> roles
              can update tenant account details. Billing administrators can still manage billing settings below.
            </p>
          </GlassPanel>
        )}
        {settingsContent}
      </div>
    </section>
  );
}
