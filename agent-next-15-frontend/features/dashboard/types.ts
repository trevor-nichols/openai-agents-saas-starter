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

export interface RecentConversationSummary {
  id: string;
  title: string;
  updatedAt: string;
  summary?: string;
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
  recentConversations: RecentConversationSummary[];
  isLoadingConversations: boolean;
  conversationsError: string | null;
  billingPreview: BillingPreviewSummary;
  quickActions: QuickAction[];
  refreshConversations: () => void;
}
