'use client';

import { useMemo } from 'react';

import { useBillingPlans } from '@/lib/queries/billingPlans';
import type { BillingPlan } from '@/types/billing';

import type { FeatureComparisonRow, PlanCardSnapshot, PricingContentState, UsageHighlight } from '../types';
import { formatPrice } from '@/features/marketing/utils/formatters';

function formatCadence(plan: BillingPlan): string {
  return plan.interval_count > 1 ? `${plan.interval_count} ${plan.interval}s` : plan.interval;
}

function buildPlanCards(plans: BillingPlan[]): PlanCardSnapshot[] {
  if (!plans.length) {
    return [
      {
        code: 'starter',
        name: 'Starter',
        priceLabel: '$49',
        cadenceLabel: 'month',
        summary: 'Everything you need to launch an agent console.',
        badges: ['Best for teams new to GPT-5'],
        highlights: ['Streaming chat workspace', 'Tenant auth + JWT refresh', 'Stripe-ready billing flows'],
      },
    ];
  }

  return plans.map((plan) => ({
    code: plan.code,
    name: plan.name,
    priceLabel:
      plan.price_cents != null ? formatPrice(plan.price_cents / 100, plan.currency) : 'Custom pricing',
    cadenceLabel: formatCadence(plan),
    summary: plan.features?.[0]?.description ?? 'Flexible tier for modern agent SaaS launches.',
    badges: [
      plan.trial_days ? `${plan.trial_days} day trial` : null,
      plan.seat_included ? `${plan.seat_included} seats included` : null,
      plan.is_active === false ? 'Retired' : null,
    ].filter(Boolean) as string[],
    highlights: (plan.features ?? []).slice(0, 3).map((feature) => feature.display_name),
  }));
}

function buildComparisonRows(plans: BillingPlan[]): FeatureComparisonRow[] {
  const rows = new Map<string, FeatureComparisonRow>();

  plans.forEach((plan) => {
    (plan.features ?? []).forEach((feature) => {
      if (!rows.has(feature.key)) {
        rows.set(feature.key, {
          featureKey: feature.key,
          label: feature.display_name,
          description: feature.description ?? undefined,
          availability: {},
        });
      }
      const row = rows.get(feature.key)!;
      row.availability[plan.code] = feature.description
        ?? (feature.is_metered ? 'Metered' : 'Included');
    });
  });

  return Array.from(rows.values()).slice(0, 6);
}

function buildUsageHighlights(plans: BillingPlan[]): UsageHighlight[] {
  if (!plans.length) {
    return [
      { label: 'Trial access', value: '14 days', helperText: 'Full platform access before committing.' },
      { label: 'Seats included', value: 'Up to 10', helperText: 'Scale without extra billing setup.' },
      { label: 'Billing automation', value: 'Live now', helperText: 'SSE plan updates + retries.' },
    ];
  }

  const maxTrial = Math.max(...plans.map((plan) => plan.trial_days ?? 0));
  const maxSeats = Math.max(...plans.map((plan) => plan.seat_included ?? 0));
  const priceRange = plans.reduce(
    (acc, plan) => {
      if (plan.price_cents != null) {
        const price = plan.price_cents / 100;
        return {
          min: Math.min(acc.min, price),
          max: Math.max(acc.max, price),
          currency: plan.currency,
        };
      }
      return acc;
    },
    { min: Number.POSITIVE_INFINITY, max: 0, currency: 'USD' },
  );

  const highlights: UsageHighlight[] = [];
  if (priceRange.min !== Number.POSITIVE_INFINITY) {
    highlights.push({
      label: 'Plan range',
      value: `${formatPrice(priceRange.min, priceRange.currency)} – ${formatPrice(priceRange.max, priceRange.currency)}`,
      helperText: 'Swap tiers anytime from the billing workspace.',
    });
  }
  if (maxTrial > 0) {
    highlights.push({
      label: 'Trial access',
      value: `${maxTrial} days`,
      helperText: 'Invite stakeholders before upgrading.',
    });
  }
  if (maxSeats > 0) {
    highlights.push({
      label: 'Seats included',
      value: `${maxSeats}+`,
      helperText: 'Service accounts + user seats managed in-app.',
    });
  }

  return highlights.slice(0, 3);
}

export function usePricingContent(): PricingContentState {
  const { plans, isLoading } = useBillingPlans();

  const planCards = useMemo(() => buildPlanCards(plans), [plans]);
  const comparisonRows = useMemo(() => buildComparisonRows(plans), [plans]);
  const usageHighlights = useMemo(() => buildUsageHighlights(plans), [plans]);

  return {
    planCards,
    comparisonRows,
    usageHighlights,
    planOrder: plans,
    isLoading,
  };
}
