import type { BillingEvent, BillingStreamStatus } from '@/types/billing';
import type { LucideIcon } from 'lucide-react';
import type { ReactNode } from 'react';

export type TrendTone = 'positive' | 'negative' | 'neutral';

export interface DashboardKpi {
  id: string;
  label: string;
  value: ReactNode;
  helperText?: string;
  icon?: ReactNode;
  trend?: {
    value: string;
    tone?: TrendTone;
    label?: string;
  };
}

export interface QuickAction {
  id: string;
  label: string;
  description: string;
  href: string;
  icon: LucideIcon;
}

export interface ActivityFeedItem {
  id: string;
  title: string;
  detail: string;
  status: 'success' | 'failure' | 'pending';
  timestamp: string;
  metadataSummary?: string | null;
}

export interface BillingPreviewSummary {
  planCode: string;
  planStatus: string;
  streamStatus: BillingStreamStatus;
  nextInvoiceLabel?: string;
  latestEvents: BillingEvent[];
}

export interface DashboardData {
  kpis: DashboardKpi[];
  isLoadingKpis: boolean;
  kpiError: string | null;
  activityFeed: ActivityFeedItem[];
  isLoadingActivity: boolean;
  activityError: string | null;
  billingPreview: BillingPreviewSummary;
  quickActions: QuickAction[];
  refreshActivity: () => void;
}
