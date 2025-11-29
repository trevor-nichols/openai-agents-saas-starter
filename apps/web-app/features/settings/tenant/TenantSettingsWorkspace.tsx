'use client';

import { GlassPanel, SectionHeader } from '@/components/ui/foundation';
import { SkeletonPanel, ErrorState } from '@/components/ui/states';
import { useTenantSettingsQuery, useUpdateTenantSettingsMutation } from '@/lib/queries/tenantSettings';
import type { BillingContact } from '@/types/tenantSettings';

import { BillingContactsCard, PlanMetadataCard, TenantFlagsCard, WebhookSettingsCard } from './components';

export function TenantSettingsWorkspace() {
  const { data, isLoading, error, refetch } = useTenantSettingsQuery();
  const updateMutation = useUpdateTenantSettingsMutation();

  const lastUpdated = data?.updatedAt
    ? new Intl.DateTimeFormat('en-US', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(data.updatedAt))
    : null;

  if (error) {
    return (
      <section className="space-y-6">
        <SectionHeader
          eyebrow="Settings"
          title="Tenant settings"
          description="Manage billing contacts, webhooks, plan metadata, and feature toggles."
        />
        <ErrorState
          title="Unable to load tenant settings"
          message={error.message}
          onRetry={() => refetch()}
        />
      </section>
    );
  }

  if (isLoading || !data) {
    return (
      <section className="space-y-6">
        <SectionHeader
          eyebrow="Settings"
          title="Tenant settings"
          description="Manage billing contacts, webhooks, plan metadata, and feature toggles."
        />
        <div className="space-y-4">
          <SkeletonPanel lines={6} />
          <SkeletonPanel lines={4} />
          <SkeletonPanel lines={4} />
          <SkeletonPanel lines={4} />
        </div>
      </section>
    );
  }

  const isSaving = updateMutation.isPending;

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
        <BillingContactsCard
          contacts={data.billingContacts}
          isSaving={isSaving}
          onSubmit={handleContactsSave}
        />
        <WebhookSettingsCard
          webhookUrl={data.billingWebhookUrl}
          isSaving={isSaving}
          onSubmit={handleWebhookSave}
        />
        <PlanMetadataCard
          planMetadata={data.planMetadata}
          isSaving={isSaving}
          onSubmit={handleMetadataSave}
        />
        <TenantFlagsCard flags={data.flags} isSaving={isSaving} onSubmit={handleFlagsSave} />
      </div>
    </section>
  );
}
