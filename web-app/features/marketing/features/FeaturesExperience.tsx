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
      <section className="space-y-10 rounded-3xl border border-white/10 bg-white/5 px-6 py-8 shadow-lg shadow-black/10">
        <FeatureHero
          eyebrow="Features"
          title="Enterprise-grade building blocks for AI agent SaaS"
          description="Agents, billing, tenant settings, and ops tooling live in their own feature directories, ready to scale with your roadmap."
          primaryCta={ctaConfig.primaryCta}
          secondaryCta={ctaConfig.secondaryCta}
          navItems={navItems}
          onCtaClick={trackCtaClick}
        />
      </section>

      <section className="rounded-3xl border border-white/5 bg-background/75 px-6 py-8 backdrop-blur">
        <MetricsRow metrics={metrics} />
      </section>

      <section className="space-y-8 rounded-3xl border border-white/10 bg-white/5 px-6 py-8">
        <PillarsGrid pillars={pillars} onCtaClick={({ location, cta }) => trackCtaClick({ location, cta })} />
        <ShowcaseTabs tabs={showcaseTabs} />
      </section>

      <section className="rounded-3xl border border-white/5 bg-background/80 px-6 py-8">
        <TestimonialPanel testimonial={testimonial} />
      </section>

      <section className="rounded-3xl border border-white/10 bg-white/5 px-6 py-8">
        <FaqSection items={faq} title="Features & capabilities" description="Common questions about extending the starter." />
      </section>

      <section className="rounded-3xl border border-white/10 bg-white/5 px-6 py-8">
        <CtaBand config={ctaConfig} onCtaClick={trackCtaClick} />
      </section>
    </div>
  );
}
