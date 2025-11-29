import { useMemo } from 'react';

import type { BillingEventUsage } from '@/types/billing';
import { useBillingStream } from '@/lib/queries/billing';
import { useBillingHistory } from '@/lib/queries/billingHistory';
import { mergeBillingEvents } from '../utils/mergeEvents';

import type { BillingOverviewData, PlanSnapshot, UsageRow } from '../types';
import { formatCurrency, formatDate, formatPeriod, formatStatusLabel, resolveStatusTone } from '../utils/formatters';

const DEFAULT_CURRENCY = 'USD';

function mapUsageRow(usage: BillingEventUsage, currency: string, index: number): UsageRow {
  return {
    key: `${usage.feature_key ?? 'feature'}-${index}`,
    feature: usage.feature_key ?? 'Unknown feature',
    quantity: usage.quantity != null ? `${usage.quantity}` : '—',
    amount: formatCurrency(usage.amount_cents, currency),
    period: formatPeriod(usage.period_start, usage.period_end),
  };
}

export function useBillingOverviewData(): BillingOverviewData {
  const { events: streamEvents, status } = useBillingStream();
  const {
    events: historyEvents,
    isLoading: isHistoryLoading,
    isFetchingMore,
    hasNextPage,
    loadMore,
  } = useBillingHistory({ pageSize: 25 });

  const mergedEvents = useMemo(() => mergeBillingEvents(historyEvents, streamEvents), [historyEvents, streamEvents]);

  const subscriptionEvent = useMemo(() => mergedEvents.find((event) => event.subscription), [mergedEvents]);
  const invoiceEvent = useMemo(() => mergedEvents.find((event) => event.invoice), [mergedEvents]);

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
    const currency = invoiceEvent?.invoice?.currency ?? DEFAULT_CURRENCY;
    return mergedEvents
      .flatMap((event) => event.usage ?? [])
      .map((usage, index) => mapUsageRow(usage, currency, index));
  }, [mergedEvents, invoiceEvent]);

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
    invoiceSummary,
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
