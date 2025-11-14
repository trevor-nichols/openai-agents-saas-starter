import type { LucideIcon } from 'lucide-react';

import type { CtaLink, MarketingFaqItem } from '@/features/marketing/types';

export interface DocNavItem {
  id: string;
  label: string;
}

export interface DocSectionEntry {
  id: string;
  title: string;
  summary: string;
  bullets: readonly string[];
  badge: string;
  cta: CtaLink;
}

export interface DocResourceLink {
  label: string;
  description: string;
  href: string;
  badge: string;
}

export interface DocGuideCard {
  title: string;
  description: string;
  href: string;
  minutes: string;
  updated: string;
  badge: string;
  icon: LucideIcon;
}

export interface DocMetric {
  label: string;
  value: string;
  hint?: string;
}

export interface DocsContentState {
  heroEyebrow: string;
  heroTitle: string;
  heroDescription: string;
  heroUpdatedAt: string;
  navItems: DocNavItem[];
  sections: DocSectionEntry[];
  resources: DocResourceLink[];
  guides: DocGuideCard[];
  metrics: DocMetric[];
  faq: MarketingFaqItem[];
}
