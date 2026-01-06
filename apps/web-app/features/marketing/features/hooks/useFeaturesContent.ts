'use client';

import { useAgents } from '@/lib/queries/agents';
import { useTools } from '@/lib/queries/tools';
import { usePublicBillingPlans } from '@/lib/queries/billingPlans';
import { usePlatformStatusQuery } from '@/lib/queries/status';

import { FEATURE_NAV, FEATURE_PILLARS, SHOWCASE_TABS, FEATURES_FAQ, FEATURES_TESTIMONIAL } from '../constants';
import type { FeaturesContentState, MetricsSummary } from '../types';

export function useFeaturesContent(): FeaturesContentState {
  const { agents } = useAgents();
  const { tools } = useTools();
  const { plans } = usePublicBillingPlans();
  const { status } = usePlatformStatusQuery();

  const toolCount = Object.keys(tools ?? {}).length;

  const metrics: MetricsSummary[] = [
    {
      label: 'Agents ready',
      value: `${agents.length}+`,
      helperText: 'Add more via the Agents SDK config.',
    },
    {
      label: 'Tools wired',
      value: toolCount ? `${toolCount} tools` : 'Bring your own',
      helperText: 'Registry filters ensure per-agent scopes.',
    },
    {
      label: 'Plan catalog',
      value: `${plans.length || 3} tiers`,
      helperText: 'Stripe-ready pricing & usage.',
    },
    status?.overview
      ? {
          label: 'Platform status',
          value: status.overview.state,
          helperText: status.overview.description,
        }
      : {
          label: 'Uptime',
          value: '99.95%',
          helperText: 'Rolling 30 days',
        },
  ].slice(0, 4);

  return {
    pillars: FEATURE_PILLARS,
    navItems: FEATURE_NAV,
    showcaseTabs: SHOWCASE_TABS,
    metrics,
    faq: FEATURES_FAQ,
    testimonial: FEATURES_TESTIMONIAL,
  };
}
