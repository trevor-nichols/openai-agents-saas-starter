'use client';

import { useMemo } from 'react';

import { usePublicBillingPlans } from '@/lib/queries/billingPlans';
import { usePlatformStatusQuery } from '@/lib/queries/status';
import type { BillingPlan } from '@/types/billing';

import type { LandingContentState, MetricDatum } from '../types';
import { formatDateLabel, formatPrice } from '@/features/marketing/utils/formatters';

function summarizePlans(plans: BillingPlan[]): Array<{ name: string; price: string; cadence: string; summary: string }> {
  if (!plans.length) {
    return [
      {
        name: 'Starter',
        price: '$49',
        cadence: 'month',
        summary: 'Kick off proofs of concept with auth + chat.',
      },
      {
        name: 'Growth',
        price: '$199',
        cadence: 'month',
        summary: 'Unlock billing automation and analytics.',
      },
    ];
  }

  return plans.slice(0, 3).map((plan) => {
    const cadence = plan.interval_count > 1 ? `${plan.interval_count} ${plan.interval}s` : plan.interval;
    const formattedPrice = plan.price_cents != null
      ? formatPrice(plan.price_cents / 100, plan.currency)
      : 'Custom';
    return {
      name: plan.name,
      price: formattedPrice,
      cadence,
      summary: plan.features?.[0]?.description ?? 'Flexible billing tier',
    };
  });
}

function computeBillingSummary(plans: BillingPlan[]): MetricDatum | null {
  if (!plans.length) {
    return null;
  }
  const sorted = [...plans].sort((a, b) => (a.price_cents ?? 0) - (b.price_cents ?? 0));
  const lowest = sorted[0];
  if (!lowest) {
    return null;
  }
  const highest = sorted[sorted.length - 1] ?? lowest;
  return {
    label: 'Plan coverage',
    value: `${plans.length} tiers`,
    helperText: `${formatPrice((lowest.price_cents ?? 0) / 100, lowest.currency)} – ${formatPrice((highest.price_cents ?? 0) / 100, highest.currency)}`,
    tone: 'default',
  };
}

export function useLandingContent(): LandingContentState {
  const { plans } = usePublicBillingPlans();
  const { status, isLoading: isStatusLoading } = usePlatformStatusQuery();

  const statusMetrics: MetricDatum[] = useMemo(() => {
    if (!status) {
      return [
        {
          label: 'Global uptime',
          value: '99.95%',
          helperText: 'Rolling 30 days',
          tone: 'positive',
        },
        {
          label: 'API latency',
          value: '~120ms',
          helperText: 'us-east-1 benchmark',
          tone: 'default',
        },
        {
          label: 'Incidents this quarter',
          value: '0 major',
          helperText: 'See the status page for live feed.',
          tone: 'default',
        },
      ];
    }

    return status.uptimeMetrics.slice(0, 3).map((metric) => ({
      label: metric.label,
      value: metric.value,
      helperText: metric.helperText,
      tone: metric.trendTone === 'positive' ? 'positive' : metric.trendTone === 'warning' ? 'warning' : 'default',
    }));
  }, [status]);

  const statusSummary = status
    ? {
        label: 'Platform status',
        state: status.overview.state,
        description: status.overview.description,
        updatedAt: formatDateLabel(status.overview.updatedAt),
      }
    : null;

  return {
    metrics: {
      statusMetrics,
      billingSummary: computeBillingSummary(plans),
    },
    statusSummary,
    plansSnapshot: summarizePlans(plans),
    isStatusLoading,
  };
}
