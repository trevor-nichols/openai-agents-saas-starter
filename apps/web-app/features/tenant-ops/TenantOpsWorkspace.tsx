'use client';

import { useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { GlassPanel, InlineTag, SectionHeader } from '@/components/ui/foundation';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import { Sheet, SheetContent } from '@/components/ui/sheet';
import { useIsMobile } from '@/hooks/use-mobile';
import {
  usePlatformTenantQuery,
  usePlatformTenantsQuery,
} from '@/lib/queries/platformTenants';
import type {
  TenantAccountCreateInput,
  TenantAccountOperatorSummary,
  TenantAccountUpdateInput,
} from '@/types/tenantAccount';

import { TENANT_PAGE_LIMIT } from './constants';
import {
  TenantCreateDialog,
  TenantEditDialog,
  TenantLifecycleDialog,
  TenantOpsDetailPanel,
  TenantOpsFiltersPanel,
  TenantOpsTable,
} from './components';
import {
  getTenantPaginationMeta,
  useTenantOpsFilters,
  useTenantOpsMutations,
  useTenantOpsPagination,
  useTenantOpsSelection,
} from './hooks';
import type { TenantLifecycleAction, TenantLifecycleIntent } from './types';

export function TenantOpsWorkspace() {
  const isMobile = useIsMobile();
  const [dialogIntent, setDialogIntent] = useState<TenantLifecycleIntent | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);

  const {
    statusFilter,
    query,
    appliedQuery,
    appliedStatusLabel,
    appliedFilters,
    setStatusFilter,
    setQuery,
    applyFilters,
    resetFilters,
  } = useTenantOpsFilters();

  const pagination = useTenantOpsPagination(TENANT_PAGE_LIMIT);

  const filters = useMemo(
    () => ({
      ...appliedFilters,
      limit: pagination.limit,
      offset: pagination.offset,
    }),
    [appliedFilters, pagination.limit, pagination.offset],
  );

  const tenantsQuery = usePlatformTenantsQuery(filters);
  const tenants = tenantsQuery.data?.accounts ?? [];
  const total = tenantsQuery.data?.total ?? 0;
  const paginationMeta = getTenantPaginationMeta(total, pagination.offset, pagination.limit);

  const selection = useTenantOpsSelection({ tenants, isMobile });

  const selectedTenantQuery = usePlatformTenantQuery(selection.resolvedTenantId, {
    enabled: Boolean(selection.resolvedTenantId),
  });

  const selectedTenant = selectedTenantQuery.data ?? selection.selectedTenantSummary;

  const {
    submitLifecycle,
    createTenant,
    updateTenant,
    isSubmittingLifecycle,
    isSubmitting,
    isCreating,
    isUpdating,
  } = useTenantOpsMutations();

  const sheetOpen = isMobile && selection.detailOpen;

  const handleApply = () => {
    applyFilters();
    pagination.resetPage();
    selection.resetSelection();
  };

  const handleReset = () => {
    resetFilters();
    pagination.resetPage();
    selection.resetSelection();
  };

  const handlePrevPage = () => {
    pagination.prevPage();
    selection.resetSelection();
  };

  const handleNextPage = () => {
    pagination.nextPage();
    selection.resetSelection();
  };

  const handleAction = (action: TenantLifecycleAction, tenant: TenantAccountOperatorSummary) => {
    selection.selectTenant(tenant.id);
    setDialogIntent({ action, tenant });
  };

  const handleDetailAction = (action: TenantLifecycleAction) => {
    if (!selectedTenant) return;
    setDialogIntent({ action, tenant: selectedTenant });
  };

  const handleSubmit = async ({ reason }: { reason: string }) => {
    if (!dialogIntent) return;
    const didSubmit = await submitLifecycle({
      action: dialogIntent.action,
      tenant: dialogIntent.tenant,
      reason,
    });
    if (didSubmit) {
      setDialogIntent(null);
    }
  };

  const handleCreate = async (payload: TenantAccountCreateInput) => {
    const created = await createTenant(payload);
    if (!created) return;
    setCreateOpen(false);
    selection.selectTenant(created.id);
    if (isMobile) {
      selection.setDetailOpen(true);
    }
  };

  const handleUpdate = async (payload: TenantAccountUpdateInput) => {
    if (!selectedTenant) return;
    const updated = await updateTenant(selectedTenant.id, payload);
    if (!updated) return;
    setEditOpen(false);
  };

  const handleViewDetails = (tenantId: string) => {
    selection.openDetails(tenantId);
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
          isLoading={tenantsQuery.isFetching}
          onStatusChange={setStatusFilter}
          onQueryChange={setQuery}
          onApply={handleApply}
          onReset={handleReset}
        />
        <p className="text-xs text-foreground/60">
          Filters: {appliedStatusLabel}
          {appliedQuery ? ` · “${appliedQuery}”` : ''}
        </p>
      </GlassPanel>

      {tenantsQuery.isLoading ? (
        <SkeletonPanel lines={8} />
      ) : tenantsQuery.isError ? (
        <ErrorState
          title="Unable to load tenants"
          message={tenantsQuery.error instanceof Error ? tenantsQuery.error.message : 'Try again shortly.'}
          onRetry={() => tenantsQuery.refetch()}
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
            <Button onClick={handlePrevPage} disabled={!paginationMeta.canPrev}>
              Previous page
            </Button>
          </div>
        </GlassPanel>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[minmax(0,_1.4fr)_minmax(0,_0.9fr)]">
          <div className="space-y-4">
            <TenantOpsTable
              tenants={tenants}
              selectedTenantId={selection.resolvedTenantId}
              onSelect={selection.selectTenant}
              onViewDetails={handleViewDetails}
              onAction={handleAction}
              isBusy={isSubmittingLifecycle}
            />

            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm text-foreground/60">
                Page {paginationMeta.page} of {paginationMeta.pageCount}
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={handlePrevPage}
                  disabled={!paginationMeta.canPrev}
                >
                  Previous
                </Button>
                <Button onClick={handleNextPage} disabled={!paginationMeta.canNext}>
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

      <Sheet open={sheetOpen} onOpenChange={selection.setDetailOpen}>
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
        tenant={dialogIntent?.tenant ?? null}
        action={dialogIntent?.action ?? null}
        isSubmitting={isSubmitting}
        onSubmit={handleSubmit}
      />

      <TenantCreateDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        onSubmit={handleCreate}
        isSubmitting={isCreating}
      />

      <TenantEditDialog
        open={editOpen}
        onOpenChange={setEditOpen}
        tenant={selectedTenant}
        onSubmit={handleUpdate}
        isSubmitting={isUpdating}
      />
    </section>
  );
}
