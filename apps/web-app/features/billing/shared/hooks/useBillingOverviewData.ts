import { useMemo } from 'react';

import type { BillingUsageTotal } from '@/types/billing';
import { readClientSessionMeta } from '@/lib/auth/clientMeta';
import { useBillingStream } from '@/lib/queries/billing';
import { useBillingHistory } from '@/lib/queries/billingHistory';
import { useBillingInvoices } from '@/lib/queries/billingInvoices';
import { useBillingUsageTotals } from '@/lib/queries/billingUsageTotals';
import { useTenantSubscription } from '@/lib/queries/billingSubscriptions';
import { mergeBillingEvents } from '../utils/mergeEvents';

import type { BillingOverviewData, PlanSnapshot, UsageRow } from '../types';
import { formatCurrency, formatDate, formatPeriod, formatStatusLabel, resolveStatusTone } from '../utils/formatters';

const DEFAULT_CURRENCY = 'USD';

function mapUsageTotalRow(total: BillingUsageTotal, index: number): UsageRow {
  const unit = total.unit ? ` ${total.unit}` : '';
  return {
    key: `${total.feature_key}-${index}`,
    feature: total.feature_key || 'Unknown feature',
    quantity: `${total.quantity.toLocaleString()}${unit}`.trim(),
    amount: '—',
    period: formatPeriod(total.window_start, total.window_end),
  };
}

export function useBillingOverviewData(): BillingOverviewData {
  const meta = readClientSessionMeta();
  const tenantId = meta?.tenantId ?? null;
  const { events: streamEvents, status } = useBillingStream();
  const {
    events: historyEvents,
    isLoading: isHistoryLoading,
    isFetchingMore,
    hasNextPage,
    loadMore,
  } = useBillingHistory({ pageSize: 25 });
  const {
    invoices,
    isLoading: isInvoicesLoading,
    error: invoicesError,
  } = useBillingInvoices({ pageSize: 5 });

  const mergedEvents = useMemo(() => mergeBillingEvents(historyEvents, streamEvents), [historyEvents, streamEvents]);

  const subscriptionEvent = useMemo(() => mergedEvents.find((event) => event.subscription), [mergedEvents]);
  const invoiceEvent = useMemo(() => mergedEvents.find((event) => event.invoice), [mergedEvents]);
  const { subscription } = useTenantSubscription({ tenantId, tenantRole: null });
  const periodStart = subscription?.current_period_start ?? subscriptionEvent?.subscription?.current_period_start ?? null;
  const periodEnd = subscription?.current_period_end ?? subscriptionEvent?.subscription?.current_period_end ?? null;

  const { totals, isLoading: isTotalsLoading, error: totalsError } = useBillingUsageTotals({
    periodStart,
    periodEnd,
  });

  const planSnapshot = useMemo<PlanSnapshot>(() => {
    const subscription = subscriptionEvent?.subscription;
    const planCode = subscription?.plan_code ?? 'Plan pending';
    const planStatus = formatStatusLabel(subscription?.status);

    return {
      planCode,
      planStatus,
      seatCount: subscription?.seat_count ?? '—',
      autoRenewLabel: subscription?.auto_renew ? 'Enabled' : 'Disabled',
      currentPeriodLabel: formatPeriod(
        subscription?.current_period_start,
        subscription?.current_period_end,
      ),
      trialEndsLabel: formatDate(subscription?.trial_ends_at),
      statusTone: resolveStatusTone(subscription?.status),
      statusLabel: planStatus,
    };
  }, [subscriptionEvent]);

  const usageRows = useMemo(() => {
    return totals
      .slice()
      .sort((left, right) => right.quantity - left.quantity)
      .map((total, index) => mapUsageTotalRow(total, index));
  }, [totals]);

  const usageWindowLabel = useMemo(() => {
    if (periodStart || periodEnd) {
      return formatPeriod(periodStart, periodEnd);
    }
    if (totals.length > 0) {
      return formatPeriod(totals[0]?.window_start ?? null, totals[0]?.window_end ?? null);
    }
    return 'Current billing period';
  }, [periodStart, periodEnd, totals]);

  const invoiceSummary = useMemo(() => {
    const invoice = invoiceEvent?.invoice;
    if (!invoice) {
      return null;
    }
    return {
      amountLabel: formatCurrency(invoice.amount_due_cents, invoice.currency ?? DEFAULT_CURRENCY),
      statusLabel: invoice.status ?? 'pending',
      reason: invoice.billing_reason ?? 'Usage',
      collectionMethod: invoice.collection_method ?? 'auto',
      invoiceUrl: invoice.hosted_invoice_url ?? null,
    };
  }, [invoiceEvent]);

  return {
    planSnapshot,
    usageRows: usageRows.slice(0, 5),
    allUsageRows: usageRows,
    usageCount: usageRows.length,
    usageWindowLabel,
    usageTotalsState: {
      isLoading: isTotalsLoading,
      error: totalsError instanceof Error ? totalsError : null,
    },
    invoiceSummary,
    invoices,
    invoicesState: {
      isLoading: isInvoicesLoading,
      error: invoicesError instanceof Error ? invoicesError : null,
    },
    events: mergedEvents,
    streamStatus: status,
    historyState: {
      isLoading: isHistoryLoading,
      isFetchingMore,
      hasNextPage,
      loadMore,
    },
  };
}
