'use client';

import { CtaBand } from '@/features/marketing/components/CtaBand';
import { FaqSection } from '@/features/marketing/components/FaqSection';
import { useMarketingAnalytics } from '@/features/marketing/hooks/useMarketingAnalytics';

import { PRICING_CTA, PRICING_FAQ, PRICING_HERO_COPY } from './constants';
import { usePricingContent } from './hooks/usePricingContent';
import { PlanCardGrid, PlanComparisonTable, PricingHero, UsageHighlights } from './components';

export function PricingExperience() {
  const { planCards, comparisonRows, usageHighlights, planOrder } = usePricingContent();
  const { trackCtaClick } = useMarketingAnalytics();

  const handlePlanCta = (planCode: string) => {
    const plan = planCards.find((candidate) => candidate.code === planCode);
    if (!plan) return;
    trackCtaClick({
      location: `pricing-plan-${plan.code}`,
      cta: {
        label: `Choose ${plan.name}`,
        href: `${PRICING_HERO_COPY.primaryCta.href}?plan=${plan.code}`,
        intent: 'primary',
      },
    });
  };

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-12 px-6 py-16">
      <PricingHero
        eyebrow={PRICING_HERO_COPY.eyebrow}
        title={PRICING_HERO_COPY.title}
        description={PRICING_HERO_COPY.description}
        primaryCta={PRICING_HERO_COPY.primaryCta}
        secondaryCta={PRICING_HERO_COPY.secondaryCta}
        onCtaClick={trackCtaClick}
      />

      <PlanCardGrid
        plans={planCards}
        primaryCtaHref={PRICING_HERO_COPY.primaryCta.href}
        onPlanCtaClick={(plan) => handlePlanCta(plan.code)}
      />

      <UsageHighlights highlights={usageHighlights} />

      <PlanComparisonTable plans={planOrder} rows={comparisonRows} />

      <FaqSection items={PRICING_FAQ} title="Pricing & billing" eyebrow="FAQ" />

      <CtaBand config={PRICING_CTA} onCtaClick={trackCtaClick} />
    </div>
  );
}
