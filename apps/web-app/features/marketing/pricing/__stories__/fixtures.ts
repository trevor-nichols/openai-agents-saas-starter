import type { BillingPlan } from '@/types/billing';
import type { PlanCardSnapshot, FeatureComparisonRow, UsageHighlight } from '../types';

export const mockPlans: BillingPlan[] = [
  {
    code: 'starter',
    name: 'Starter',
    interval: 'month',
    interval_count: 1,
    price_cents: 4900,
    currency: 'USD',
    trial_days: 14,
    seat_included: 3,
    feature_toggles: {},
    is_active: true,
    features: [
      { key: 'seats', display_name: 'Seats', description: '3 seats included', hard_limit: null, soft_limit: null, is_metered: false },
      { key: 'chat', display_name: 'Chat workspace', description: 'Included', hard_limit: null, soft_limit: null, is_metered: false },
      { key: 'billing', display_name: 'Billing console', description: 'Included', hard_limit: null, soft_limit: null, is_metered: false },
    ],
  },
  {
    code: 'scale',
    name: 'Scale',
    interval: 'month',
    interval_count: 1,
    price_cents: 24900,
    currency: 'USD',
    trial_days: 0,
    seat_included: 10,
    feature_toggles: {},
    is_active: true,
    features: [
      { key: 'seats', display_name: 'Seats', description: '10 seats included', hard_limit: null, soft_limit: null, is_metered: false },
      { key: 'chat', display_name: 'Chat workspace', description: 'Included', hard_limit: null, soft_limit: null, is_metered: false },
      { key: 'billing', display_name: 'Billing console', description: 'Included', hard_limit: null, soft_limit: null, is_metered: false },
      { key: 'sso', display_name: 'SSO/SAML', description: 'Included', hard_limit: null, soft_limit: null, is_metered: false },
    ],
  },
];

export const mockPlanCards: PlanCardSnapshot[] = [
  {
    code: 'starter',
    name: 'Starter',
    priceLabel: '$49',
    cadenceLabel: 'month',
    summary: 'Launch quickly with the core agent workspace.',
    badges: ['Best for teams new to GPT-5'],
    highlights: ['Streaming chat workspace', 'Tenant auth + JWT refresh', 'Stripe-ready billing flows'],
  },
  {
    code: 'scale',
    name: 'Scale',
    priceLabel: '$249',
    cadenceLabel: 'month',
    summary: 'For production teams needing more seats and SSO.',
    badges: ['Most popular'],
    highlights: ['SSO + seat controls', 'Observability', 'Custom prompts'],
  },
];

export const mockComparisonRows: FeatureComparisonRow[] = [
  {
    featureKey: 'seats',
    label: 'Seats included',
    description: 'Built-in seat accounting across tenants.',
    availability: {
      starter: '3 seats',
      scale: '10 seats',
    },
  },
  {
    featureKey: 'sso',
    label: 'SSO/SAML',
    availability: {
      starter: '—',
      scale: 'Included',
    },
  },
];

export const mockUsageHighlights: UsageHighlight[] = [
  { label: 'Trial access', value: '14 days', helperText: 'Invite your stakeholders before upgrading.' },
  { label: 'Seats included', value: 'Up to 10', helperText: 'Service accounts plus user seats.' },
  { label: 'Billing automation', value: 'Live now', helperText: 'Streaming events + retries.' },
];
