import type { PlanChangeTiming } from '@/lib/types/billing';
import type { BillingEvent, BillingStreamStatus } from '@/types/billing';

export type StatusTone = 'positive' | 'warning' | 'default';

export interface PlanSnapshot {
  planCode: string;
  planStatus: string;
  seatCount: string | number;
  autoRenewLabel: string;
  currentPeriodLabel: string;
  trialEndsLabel: string;
  statusTone: StatusTone;
  statusLabel: string;
}

export interface UsageRow {
  key: string;
  feature: string;
  quantity: string;
  amount: string;
  period: string;
}

export interface InvoiceSummary {
  amountLabel: string;
  statusLabel: string;
  reason?: string | null;
  collectionMethod?: string | null;
  invoiceUrl?: string | null;
}

export interface BillingOverviewData {
  planSnapshot: PlanSnapshot;
  usageRows: UsageRow[];
  allUsageRows: UsageRow[];
  usageCount: number;
  usageWindowLabel: string;
  usageTotalsState: {
    isLoading: boolean;
    error: Error | null;
  };
  invoiceSummary: InvoiceSummary | null;
  events: BillingEvent[];
  streamStatus: BillingStreamStatus;
  historyState: {
    isLoading: boolean;
    isFetchingMore: boolean;
    hasNextPage: boolean;
    loadMore: () => Promise<void>;
  };
}

export interface SubscriptionSettingsFormValues {
  billingEmail: string;
  autoRenew: boolean;
  seatCount?: number;
}

export interface PlanChangeFormValues {
  billingEmail?: string;
  autoRenew?: boolean;
  seatCount?: number;
  timing?: PlanChangeTiming;
}
