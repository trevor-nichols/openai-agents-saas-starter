'use client';

import { useMemo } from 'react';

import {
  HERO_COPY,
  PROOF_POINTS,
  FEATURE_HIGHLIGHTS,
  FAQ_ITEMS,
  CTA_CONFIG,
} from './constants';
import { HeroSection, ProofPoints, FeatureHighlightsGrid, PlanShowcase, MetricsStrip } from './components';
import { CtaBand, FaqSection, StatusAlertsCard } from '@/features/marketing/components';
import { useLandingContent } from './hooks';
import { useMarketingAnalytics, useSignupCtaTarget } from '@/features/marketing/hooks';

export function LandingExperience() {
  const { metrics, statusSummary, plansSnapshot, isStatusLoading } = useLandingContent();
  const { trackCtaClick, trackLeadSubmit } = useMarketingAnalytics();
  const { cta } = useSignupCtaTarget();

  const heroCopy = useMemo(
    () => ({
      ...HERO_COPY,
      primaryCta: {
        ...HERO_COPY.primaryCta,
        href: cta.href,
        label: cta.label,
      },
    }),
    [cta],
  );

  const ctaBandConfig = useMemo(
    () => ({
      ...CTA_CONFIG,
      primaryCta: {
        ...CTA_CONFIG.primaryCta,
        href: cta.href,
        label: cta.label,
      },
    }),
    [cta],
  );

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-12 px-6 py-16">
      <HeroSection copy={heroCopy} statusSummary={statusSummary} onCtaClick={trackCtaClick} />
      <ProofPoints items={PROOF_POINTS} />
      <FeatureHighlightsGrid highlights={FEATURE_HIGHLIGHTS} />
      <PlanShowcase plans={plansSnapshot} />
      <MetricsStrip metrics={metrics} isLoading={isStatusLoading} />
      <StatusAlertsCard onLeadSubmit={trackLeadSubmit} source="landing-status-card" />
      <FaqSection items={FAQ_ITEMS} />
      <CtaBand config={ctaBandConfig} onCtaClick={trackCtaClick} />
    </div>
  );
}
