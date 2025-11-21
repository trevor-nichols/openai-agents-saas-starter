'use client';

import { useMemo } from 'react';

import { CtaBand } from '@/features/marketing/components/CtaBand';
import { FaqSection } from '@/features/marketing/components/FaqSection';
import { useMarketingAnalytics, useSignupCtaTarget } from '@/features/marketing/hooks';

import { PRICING_CTA, PRICING_FAQ, PRICING_HERO_COPY } from './constants';
import { usePricingContent } from './hooks/usePricingContent';
import { PlanCardGrid, PlanComparisonTable, PricingHero, UsageHighlights } from './components';

export function PricingExperience() {
  const { planCards, comparisonRows, usageHighlights, planOrder } = usePricingContent();
  const { trackCtaClick } = useMarketingAnalytics();
  const { cta } = useSignupCtaTarget();

  const heroCopy = useMemo(
    () => ({
      ...PRICING_HERO_COPY,
      primaryCta: { ...PRICING_HERO_COPY.primaryCta, href: cta.href, label: cta.label },
    }),
    [cta],
  );

  const ctaBandConfig = useMemo(
    () => ({
      ...PRICING_CTA,
      primaryCta: { ...PRICING_CTA.primaryCta, href: cta.href, label: cta.label },
    }),
    [cta],
  );

  const handlePlanCta = (planCode: string) => {
    const plan = planCards.find((candidate) => candidate.code === planCode);
    if (!plan) return;
    trackCtaClick({
      location: `pricing-plan-${plan.code}`,
      cta: {
        label: `Choose ${plan.name}`,
        href: `${cta.href}?plan=${plan.code}`,
        intent: 'primary',
      },
    });
  };

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-12 px-6 py-16">
      <PricingHero
        eyebrow={heroCopy.eyebrow}
        title={heroCopy.title}
        description={heroCopy.description}
        primaryCta={heroCopy.primaryCta}
        secondaryCta={heroCopy.secondaryCta}
        onCtaClick={trackCtaClick}
      />

      <PlanCardGrid
        plans={planCards}
        primaryCtaHref={cta.href}
        onPlanCtaClick={(plan) => handlePlanCta(plan.code)}
      />

      <UsageHighlights highlights={usageHighlights} />

      <PlanComparisonTable plans={planOrder} rows={comparisonRows} />

      <FaqSection items={PRICING_FAQ} title="Pricing & billing" eyebrow="FAQ" />

      <CtaBand config={ctaBandConfig} onCtaClick={trackCtaClick} />
    </div>
  );
}
