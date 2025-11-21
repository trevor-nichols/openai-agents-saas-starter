import type { LucideIcon } from 'lucide-react';

import type { CtaLink, CtaConfig as SharedCtaConfig, MarketingFaqItem } from '@/features/marketing/types';

export interface HeroCopy {
  eyebrow: string;
  title: string;
  description: string;
  primaryCta: CtaLink;
  secondaryCta: CtaLink;
}

export interface ProofPoint {
  label: string;
  value: string;
}

export interface FeatureHighlight {
  icon: LucideIcon;
  title: string;
  description: string;
  bullets: readonly string[];
}

export interface MetricDatum {
  label: string;
  value: string;
  helperText?: string;
  tone?: 'default' | 'positive' | 'warning';
}

export type FaqItem = MarketingFaqItem;

export type CtaConfig = SharedCtaConfig;

export interface LandingMetrics {
  statusMetrics: MetricDatum[];
  billingSummary: MetricDatum | null;
}

export interface StatusSummary {
  label: string;
  state: string;
  description: string;
  updatedAt: string;
}

export interface LandingContentState {
  metrics: LandingMetrics;
  statusSummary: StatusSummary | null;
  plansSnapshot: Array<{ name: string; price: string; cadence: string; summary: string }>;
  isStatusLoading: boolean;
}
