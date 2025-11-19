'use client';

import { useMemo } from 'react';

import { CtaBand, FaqSection } from '@/features/marketing/components';
import { useMarketingAnalytics, useSignupCtaTarget } from '@/features/marketing/hooks';

import { FEATURES_CTA } from './constants';
import { FeatureHero, PillarsGrid, ShowcaseTabs, MetricsRow, TestimonialPanel } from './components';
import { useFeaturesContent } from './hooks/useFeaturesContent';

export function FeaturesExperience() {
  const { pillars, navItems, showcaseTabs, metrics, faq, testimonial } = useFeaturesContent();
  const { trackCtaClick } = useMarketingAnalytics();
  const { cta } = useSignupCtaTarget();

  const ctaConfig = useMemo(
    () => ({
      ...FEATURES_CTA,
      primaryCta: { ...FEATURES_CTA.primaryCta, href: cta.href, label: cta.label },
    }),
    [cta],
  );

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-12 px-6 py-16">
      <FeatureHero
        eyebrow="Features"
        title="Enterprise-grade building blocks for AI agent SaaS"
        description="Agents, billing, tenant settings, and ops tooling live in their own feature directories, ready to scale with your roadmap."
        primaryCta={ctaConfig.primaryCta}
        secondaryCta={ctaConfig.secondaryCta}
        navItems={navItems}
        onCtaClick={trackCtaClick}
      />

      <MetricsRow metrics={metrics} />

      <PillarsGrid pillars={pillars} onCtaClick={({ location, cta }) => trackCtaClick({ location, cta })} />

      <ShowcaseTabs tabs={showcaseTabs} />

      <TestimonialPanel testimonial={testimonial} />

      <FaqSection items={faq} title="Features & capabilities" description="Common questions about extending the starter." />

      <CtaBand config={ctaConfig} onCtaClick={trackCtaClick} />
    </div>
  );
}
