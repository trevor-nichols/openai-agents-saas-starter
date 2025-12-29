'use client';

import type { ColumnDef } from '@tanstack/react-table';

import { useMemo } from 'react';

import { SectionHeader } from '@/components/ui/foundation';
import { DataTable } from '@/components/ui/data-table';
import { EmptyState } from '@/components/ui/states';
import { readClientSessionMeta } from '@/lib/auth/clientMeta';
import { useBillingUsageTotals } from '@/lib/queries/billingUsageTotals';
import { useTenantSubscription } from '@/lib/queries/billingSubscriptions';

import { BILLING_COPY } from '../shared/constants';
import type { UsageRow } from '../shared/types';
import { formatPeriod } from '../shared/utils/formatters';

const usageColumns: ColumnDef<UsageRow>[] = [
  {
    header: 'Feature',
    accessorKey: 'feature',
  },
  {
    header: 'Quantity',
    accessorKey: 'quantity',
    cell: ({ getValue }) => <span className="text-right">{getValue<string>()}</span>,
  },
  {
    header: 'Amount',
    accessorKey: 'amount',
    cell: ({ getValue }) => <span className="text-right">{getValue<string>()}</span>,
  },
  {
    header: 'Period',
    accessorKey: 'period',
    cell: ({ getValue }) => <span className="text-right">{getValue<string>()}</span>,
  },
];

export function UsageLedger() {
  const meta = readClientSessionMeta();
  const tenantId = meta?.tenantId ?? null;
  const { subscription } = useTenantSubscription({ tenantId, tenantRole: null });
  const periodStart = subscription?.current_period_start ?? null;
  const periodEnd = subscription?.current_period_end ?? null;

  const { totals, isLoading, error } = useBillingUsageTotals({
    periodStart,
    periodEnd,
  });

  const usageRows = useMemo<UsageRow[]>(
    () =>
      totals.map((total, index) => ({
        key: `${total.feature_key}-${index}`,
        feature: total.feature_key || 'Unknown feature',
        quantity: `${total.quantity.toLocaleString()} ${total.unit}`.trim(),
        amount: '—',
        period: formatPeriod(total.window_start, total.window_end),
      })),
    [totals],
  );

  return (
    <section className="space-y-8">
      <SectionHeader
        eyebrow={BILLING_COPY.usagePage.eyebrow}
        title={BILLING_COPY.usagePage.title}
        description={BILLING_COPY.usagePage.description}
      />

      <DataTable
        columns={usageColumns}
        data={usageRows}
        isLoading={isLoading}
        isError={Boolean(error)}
        error={error?.message}
        emptyState={
          <EmptyState
            title="No usage recorded"
            description="Metered features will populate this ledger once they emit events."
          />
        }
        enablePagination
      />
    </section>
  );
}
