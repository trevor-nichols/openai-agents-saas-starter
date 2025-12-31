'use client';

import { useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { GlassPanel, InlineTag, SectionHeader } from '@/components/ui/foundation';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import { Sheet, SheetContent } from '@/components/ui/sheet';
import { useToast } from '@/components/ui/use-toast';
import { useIsMobile } from '@/hooks/use-mobile';
import {
  useCreatePlatformTenantMutation,
  useDeprovisionPlatformTenantMutation,
  usePlatformTenantQuery,
  usePlatformTenantsQuery,
  useReactivatePlatformTenantMutation,
  useSuspendPlatformTenantMutation,
  useUpdatePlatformTenantMutation,
} from '@/lib/queries/platformTenants';
import type {
  TenantAccountCreateInput,
  TenantAccountOperatorSummary,
  TenantAccountUpdateInput,
} from '@/types/tenantAccount';

import { TENANT_STATUS_OPTIONS, type TenantStatusFilter } from './constants';
import {
  TenantCreateDialog,
  TenantEditDialog,
  TenantLifecycleDialog,
  TenantOpsDetailPanel,
  TenantOpsFiltersPanel,
  TenantOpsTable,
} from './components';
import type { TenantLifecycleAction, TenantLifecycleIntent } from './types';

const DEFAULT_LIMIT = 25;

function resolveStatusFilter(status: TenantStatusFilter) {
  return status === 'all' ? undefined : status;
}

const ACTION_RESULT_COPY: Record<TenantLifecycleAction, string> = {
  suspend: 'suspended',
  reactivate: 'reactivated',
  deprovision: 'deprovisioned',
};

export function TenantOpsWorkspace() {
  const toast = useToast();
  const isMobile = useIsMobile();
  const [statusFilter, setStatusFilter] = useState<TenantStatusFilter>('active');
  const [query, setQuery] = useState('');
  const [appliedStatus, setAppliedStatus] = useState<TenantStatusFilter>('active');
  const [appliedQuery, setAppliedQuery] = useState('');
  const [offset, setOffset] = useState(0);
  const [dialogIntent, setDialogIntent] = useState<TenantLifecycleIntent | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedTenantId, setSelectedTenantId] = useState<string | null>(null);

  const filters = useMemo(
    () => ({
      status: resolveStatusFilter(appliedStatus),
      q: appliedQuery || undefined,
      limit: DEFAULT_LIMIT,
      offset,
    }),
    [appliedStatus, appliedQuery, offset],
  );

  const { data, isLoading, isError, error, refetch, isFetching } = usePlatformTenantsQuery(filters);
  const suspendMutation = useSuspendPlatformTenantMutation();
  const reactivateMutation = useReactivatePlatformTenantMutation();
  const deprovisionMutation = useDeprovisionPlatformTenantMutation();
  const createMutation = useCreatePlatformTenantMutation();
  const updateMutation = useUpdatePlatformTenantMutation();

  const total = data?.total ?? 0;
  const tenants = useMemo(() => data?.accounts ?? [], [data?.accounts]);
  const canPrev = offset > 0;
  const canNext = offset + DEFAULT_LIMIT < total;
  const pageCount = Math.max(1, Math.ceil(total / DEFAULT_LIMIT));
  const page = Math.floor(offset / DEFAULT_LIMIT) + 1;

  const resolvedTenantId = useMemo(
    () => selectedTenantId ?? tenants[0]?.id ?? null,
    [selectedTenantId, tenants],
  );

  const selectedTenantQuery = usePlatformTenantQuery(resolvedTenantId, {
    enabled: Boolean(resolvedTenantId),
  });

  const selectedTenantSummary = useMemo(
    () => tenants.find((tenant) => tenant.id === resolvedTenantId) ?? null,
    [tenants, resolvedTenantId],
  );
  const selectedTenant = selectedTenantQuery.data ?? selectedTenantSummary;

  const activeAction = dialogIntent?.action ?? null;
  const activeTenant = dialogIntent?.tenant ?? null;

  const isSubmittingLifecycle =
    suspendMutation.isPending || reactivateMutation.isPending || deprovisionMutation.isPending;
  const isSubmitting = isSubmittingLifecycle || createMutation.isPending || updateMutation.isPending;
  const sheetOpen = isMobile && detailOpen;

  const handleApply = () => {
    setAppliedStatus(statusFilter);
    setAppliedQuery(query.trim());
    setOffset(0);
    setSelectedTenantId(null);
  };

  const handleReset = () => {
    setStatusFilter('active');
    setQuery('');
    setAppliedStatus('active');
    setAppliedQuery('');
    setOffset(0);
    setSelectedTenantId(null);
  };

  const handlePrevPage = () => {
    setOffset((current) => Math.max(0, current - DEFAULT_LIMIT));
    setSelectedTenantId(null);
  };

  const handleNextPage = () => {
    setOffset((current) => current + DEFAULT_LIMIT);
    setSelectedTenantId(null);
  };

  const handleAction = (action: TenantLifecycleAction, tenant: TenantAccountOperatorSummary) => {
    setSelectedTenantId(tenant.id);
    setDialogIntent({ action, tenant });
  };

  const handleDetailAction = (action: TenantLifecycleAction) => {
    if (!selectedTenant) return;
    setDialogIntent({ action, tenant: selectedTenant });
  };

  const handleSubmit = async ({ reason }: { reason: string }) => {
    if (!activeAction || !activeTenant) return;
    try {
      if (activeAction === 'suspend') {
        await suspendMutation.mutateAsync({ tenantId: activeTenant.id, payload: { reason } });
      } else if (activeAction === 'reactivate') {
        await reactivateMutation.mutateAsync({ tenantId: activeTenant.id, payload: { reason } });
      } else {
        await deprovisionMutation.mutateAsync({ tenantId: activeTenant.id, payload: { reason } });
      }
      toast.success({
        title: 'Tenant updated',
        description: `${activeTenant.name} is now ${ACTION_RESULT_COPY[activeAction]}.`,
      });
      setDialogIntent(null);
    } catch (err) {
      toast.error({
        title: 'Unable to update tenant',
        description: err instanceof Error ? err.message : 'Try again shortly.',
      });
    }
  };

  const handleCreate = async (payload: TenantAccountCreateInput) => {
    try {
      const created = await createMutation.mutateAsync({
        name: payload.name,
        slug: payload.slug ?? undefined,
      });
      toast.success({
        title: 'Tenant created',
        description: `${created.name} is ready for provisioning.`,
      });
      setCreateOpen(false);
      setSelectedTenantId(created.id);
      setDetailOpen(isMobile);
    } catch (err) {
      toast.error({
        title: 'Unable to create tenant',
        description: err instanceof Error ? err.message : 'Try again shortly.',
      });
    }
  };

  const handleUpdate = async (payload: TenantAccountUpdateInput) => {
    if (!selectedTenant) return;
    try {
      const updated = await updateMutation.mutateAsync({
        tenantId: selectedTenant.id,
        payload,
      });
      toast.success({
        title: 'Tenant updated',
        description: `${updated.name} details were saved.`,
      });
      setEditOpen(false);
    } catch (err) {
      toast.error({
        title: 'Unable to update tenant',
        description: err instanceof Error ? err.message : 'Try again shortly.',
      });
    }
  };

  const handleViewDetails = (tenantId: string) => {
    setSelectedTenantId(tenantId);
    if (isMobile) {
      setDetailOpen(true);
    }
  };

  return (
    <section className="space-y-6">
      <GlassPanel className="space-y-3">
        <SectionHeader
          eyebrow="Operations"
          title="Tenant lifecycle"
          description="Review tenant status, search across the platform, and trigger lifecycle actions."
          actions={(
            <>
              <InlineTag tone="default">{total} tenants</InlineTag>
              <Button onClick={() => setCreateOpen(true)}>Create tenant</Button>
            </>
          )}
        />
        <TenantOpsFiltersPanel
          status={statusFilter}
          query={query}
          isLoading={isFetching}
          onStatusChange={setStatusFilter}
          onQueryChange={setQuery}
          onApply={handleApply}
          onReset={handleReset}
        />
        <p className="text-xs text-foreground/60">
          Filters: {TENANT_STATUS_OPTIONS.find((option) => option.value === appliedStatus)?.label ?? 'Active'}{' '}
          {appliedQuery ? `· “${appliedQuery}”` : ''}
        </p>
      </GlassPanel>

      {isLoading ? (
        <SkeletonPanel lines={8} />
      ) : isError ? (
        <ErrorState
          title="Unable to load tenants"
          message={error instanceof Error ? error.message : 'Try again shortly.'}
          onRetry={() => refetch()}
        />
      ) : total === 0 ? (
        <EmptyState
          title="No tenants found"
          description="Try adjusting filters or create a new tenant."
          action={<Button onClick={() => setCreateOpen(true)}>Create tenant</Button>}
        />
      ) : tenants.length === 0 ? (
        <GlassPanel className="space-y-3">
          <p className="text-base font-semibold text-foreground">No tenants on this page</p>
          <p className="text-sm text-foreground/70">
            Your current filters or page offset returned no results. Reset filters or move back a page to continue.
          </p>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={handleReset}>
              Reset filters
            </Button>
            <Button onClick={handlePrevPage} disabled={!canPrev}>
              Previous page
            </Button>
          </div>
        </GlassPanel>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[minmax(0,_1.4fr)_minmax(0,_0.9fr)]">
          <div className="space-y-4">
            <TenantOpsTable
              tenants={tenants}
              selectedTenantId={resolvedTenantId}
              onSelect={setSelectedTenantId}
              onViewDetails={handleViewDetails}
              onAction={handleAction}
              isBusy={isSubmittingLifecycle}
            />

            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm text-foreground/60">
                Page {page} of {pageCount}
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={handlePrevPage}
                  disabled={!canPrev}
                >
                  Previous
                </Button>
                <Button onClick={handleNextPage} disabled={!canNext}>
                  Next
                </Button>
              </div>
            </div>
          </div>

          <div className="hidden lg:block">
            <TenantOpsDetailPanel
              tenant={selectedTenant}
              isLoading={selectedTenantQuery.isLoading}
              error={(selectedTenantQuery.error as Error) ?? null}
              onRetry={() => selectedTenantQuery.refetch()}
              onEdit={() => setEditOpen(true)}
              onCreate={() => setCreateOpen(true)}
              onAction={handleDetailAction}
              isBusy={isSubmitting}
            />
          </div>
        </div>
      )}

      <Sheet open={sheetOpen} onOpenChange={setDetailOpen}>
        <SheetContent className="w-full space-y-6 sm:max-w-lg">
          <TenantOpsDetailPanel
            variant="plain"
            tenant={selectedTenant}
            isLoading={selectedTenantQuery.isLoading}
            error={(selectedTenantQuery.error as Error) ?? null}
            onRetry={() => selectedTenantQuery.refetch()}
            onEdit={() => setEditOpen(true)}
            onCreate={() => setCreateOpen(true)}
            onAction={handleDetailAction}
            isBusy={isSubmitting}
          />
        </SheetContent>
      </Sheet>

      <TenantLifecycleDialog
        open={Boolean(dialogIntent)}
        onOpenChange={(open) => {
          if (!open) setDialogIntent(null);
        }}
        tenant={activeTenant}
        action={activeAction}
        isSubmitting={isSubmitting}
        onSubmit={handleSubmit}
      />

      <TenantCreateDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        onSubmit={handleCreate}
        isSubmitting={createMutation.isPending}
      />

      <TenantEditDialog
        open={editOpen}
        onOpenChange={setEditOpen}
        tenant={selectedTenant}
        onSubmit={handleUpdate}
        isSubmitting={updateMutation.isPending}
      />
    </section>
  );
}
