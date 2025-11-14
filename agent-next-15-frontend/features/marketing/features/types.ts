import type { LucideIcon } from 'lucide-react';

import type { CtaLink, MarketingFaqItem } from '@/features/marketing/types';

export interface FeatureNavItem {
  id: string;
  label: string;
}

export interface FeaturePillar {
  id: string;
  title: string;
  description: string;
  bullets: string[];
  icon: LucideIcon;
  cta: CtaLink;
}

export interface ShowcaseTab {
  id: string;
  label: string;
  title: string;
  description: string;
  bullets: string[];
}

export interface MetricsSummary {
  label: string;
  value: string;
  helperText?: string;
}

export interface Testimonial {
  quote: string;
  author: string;
  role: string;
}

export interface FeaturesContentState {
  pillars: FeaturePillar[];
  navItems: FeatureNavItem[];
  showcaseTabs: ShowcaseTab[];
  metrics: MetricsSummary[];
  faq: MarketingFaqItem[];
  testimonial: Testimonial;
}
