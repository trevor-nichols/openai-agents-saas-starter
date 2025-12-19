import {
  CTA_CONFIG,
  FEATURE_HIGHLIGHTS,
  HERO_COPY,
  LOGO_ITEMS,
  PROOF_POINTS,
  SHOWCASE_TABS,
  TESTIMONIALS,
} from '../constants';
import type { CtaConfig, HeroCopy, LandingContentState, LandingMetrics, StatusSummary } from '../types';
import type { ShowcaseTab } from '@/features/marketing/features/types';
import type { Testimonial } from '@/components/ui/testimonials';

export const heroCopy: HeroCopy = HERO_COPY;

export const statusSummary: StatusSummary = {
  label: 'Platform status',
  state: 'Operational',
  description: 'All systems healthy with live SSE streams and status feeds.',
  updatedAt: '5m ago',
};

export const landingMetrics: LandingMetrics = {
  statusMetrics: [
    { label: 'Global uptime', value: '99.95%', helperText: 'Rolling 30 days', tone: 'positive' },
    { label: 'API latency', value: '120ms', helperText: 'us-east-1 benchmark', tone: 'default' },
    { label: 'Incidents this quarter', value: '0 major', helperText: 'Live RSS feed ready', tone: 'default' },
  ],
  billingSummary: {
    label: 'Plan coverage',
    value: '3 tiers',
    helperText: '$49 – $249',
    tone: 'default',
  },
};

export const plansSnapshot: LandingContentState['plansSnapshot'] = [
  { name: 'Starter', price: '$49', cadence: 'month', summary: 'Auth, chat, and status ready to brand.' },
  { name: 'Growth', price: '$199', cadence: 'month', summary: 'Billing + analytics wiring included.' },
  { name: 'Enterprise', price: 'Custom', cadence: 'annual', summary: 'Compliance and advanced operations.' },
];

export const logos = LOGO_ITEMS;

export const testimonials: Testimonial[] = TESTIMONIALS;

export const showcaseTabs: ShowcaseTab[] = SHOWCASE_TABS;

export const ctaConfig: CtaConfig = CTA_CONFIG;

export const featureHighlights = FEATURE_HIGHLIGHTS;

export const proofPoints = PROOF_POINTS;
