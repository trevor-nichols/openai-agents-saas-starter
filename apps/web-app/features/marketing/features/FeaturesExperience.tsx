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
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-16 px-6 py-12 lg:py-24">
      <FeatureHero
        eyebrow="Features"
        title="Enterprise-grade building blocks for AI agent SaaS"
        description="Agents, billing, tenant settings, and ops tooling live in their own feature directories, ready to scale with your roadmap."
        primaryCta={ctaConfig.primaryCta}
        secondaryCta={ctaConfig.secondaryCta}
        navItems={navItems}
        onCtaClick={trackCtaClick}
      />

      <section className="w-full">
        <MetricsRow metrics={metrics} />
      </section>

      <section className="space-y-8 rounded-3xl border border-white/10 bg-white/5 px-6 py-12">
        <PillarsGrid pillars={pillars} onCtaClick={({ location, cta }) => trackCtaClick({ location, cta })} />
        <ShowcaseTabs tabs={showcaseTabs} />
      </section>

      <section className="rounded-3xl border border-white/5 bg-background/80 px-6 py-12">
        <TestimonialPanel testimonial={testimonial} />
      </section>

      <section className="rounded-3xl border border-white/10 bg-white/5 px-6 py-12">
        <FaqSection items={faq} title="Features & capabilities" description="Common questions about extending the starter." />
      </section>

      <section className="rounded-3xl border border-white/10 bg-white/5 px-6 py-12">
        <CtaBand config={ctaConfig} onCtaClick={trackCtaClick} />
      </section>
    </div>
  );
}
