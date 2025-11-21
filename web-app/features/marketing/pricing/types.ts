import type { BillingPlan } from '@/types/billing';

export interface PlanCardSnapshot {
  code: string;
  name: string;
  priceLabel: string;
  cadenceLabel: string;
  summary: string;
  badges: string[];
  highlights: string[];
}

export interface FeatureComparisonRow {
  featureKey: string;
  label: string;
  description?: string;
  availability: Record<string, string>;
}

export interface UsageHighlight {
  label: string;
  value: string;
  helperText?: string;
}

export interface PricingContentState {
  planCards: PlanCardSnapshot[];
  comparisonRows: FeatureComparisonRow[];
  usageHighlights: UsageHighlight[];
  planOrder: BillingPlan[];
  isLoading: boolean;
}
