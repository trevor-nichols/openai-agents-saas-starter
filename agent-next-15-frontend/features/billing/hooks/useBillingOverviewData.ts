import { useMemo } from 'react';

import type { BillingEventUsage } from '@/types/billing';
import { useBillingStream } from '@/lib/queries/billing';

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
  const { events, status } = useBillingStream();

  const subscriptionEvent = useMemo(() => events.find((event) => event.subscription), [events]);
  const invoiceEvent = useMemo(() => events.find((event) => event.invoice), [events]);

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
    return events
      .flatMap((event) => event.usage ?? [])
      .map((usage, index) => mapUsageRow(usage, currency, index));
  }, [events, invoiceEvent]);

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
    events,
    streamStatus: status,
  };
}
