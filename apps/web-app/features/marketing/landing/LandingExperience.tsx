'use client';

import { useMemo } from 'react';

import {
  HERO_COPY,
  PROOF_POINTS,
  FEATURE_HIGHLIGHTS,
  FAQ_ITEMS,
  CTA_CONFIG,
  LOGO_ITEMS,
  TESTIMONIALS,
  SHOWCASE_TABS,
  OPERATOR_BULLETS,
} from './constants';
import {
  HeroSection,
  FeatureHighlightsGrid,
  PlanShowcase,
  MetricsStrip,
  SocialProofMarquee,
  ShowcaseSplit,
  TestimonialsSection,
} from './components';
import { CtaBand, FaqSection, StatusAlertsCard } from '@/features/marketing/components';
import { useLandingContent } from './hooks';
import { useMarketingAnalytics, useSignupCtaTarget } from '@/features/marketing/hooks';
import { Button } from '@/components/ui/button';
import { StatCard, SectionHeader } from '@/components/ui/foundation';
import Link from 'next/link';

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
    <div className="-mt-10 flex w-full flex-col gap-16 pb-16 lg:-mt-14">
      <HeroSection copy={heroCopy} statusSummary={statusSummary} onCtaClick={trackCtaClick} />

      <SocialProofMarquee logos={LOGO_ITEMS} />

      <div className="mx-auto w-full max-w-6xl space-y-16 px-6">
        <section className="grid items-start gap-10 md:grid-cols-12">
          <div className="space-y-6 md:col-span-5">
            <p className="text-xs uppercase tracking-[0.3em] text-primary">Built for fast launches</p>
            <h2 className="text-4xl font-semibold leading-tight text-foreground sm:text-5xl">A production foundation you can brand in days</h2>
            <p className="text-lg text-foreground/70">
              Keep the agent console, billing surfaces, and ops rails intact while you focus on the workflows that make your product unique.
            </p>
            <ul className="space-y-2 text-foreground/80">
              <li>• Clone, hydrate envs with Starter CLI, deploy.</li>
              <li>• Auth, RBAC, billing, status, and observability already wired.</li>
              <li>• Feature directories keep UI and data flows organized.</li>
            </ul>
            <Button size="lg" variant="secondary" asChild>
              <Link href="/features">Explore the feature map</Link>
            </Button>
          </div>
          <div className="md:col-span-7">
            <FeatureHighlightsGrid highlights={FEATURE_HIGHLIGHTS} />
          </div>
        </section>
      </div>

      <section className="relative w-full rounded-3xl bg-gradient-to-r from-primary/5 via-background to-primary/5 px-6 py-12">
        <div className="mx-auto grid w-full max-w-6xl gap-4 sm:grid-cols-2 md:grid-cols-3">
          {PROOF_POINTS.map((item) => (
            <StatCard key={item.label} label={item.label} value={item.value} />
          ))}
        </div>
      </section>

      <ShowcaseSplit tabs={SHOWCASE_TABS} />

      <TestimonialsSection testimonials={TESTIMONIALS} />

      <section className="mx-auto w-full max-w-6xl space-y-10 px-6">
        <div className="grid gap-8 md:grid-cols-12">
          <div className="md:col-span-8">
            <PlanShowcase plans={plansSnapshot} />
          </div>
          <div className="md:col-span-4 space-y-4">
            <SectionHeader
              eyebrow="Operations"
              title="Live telemetry"
              description="Usage, uptime, and billing coverage update in real time."
            />
            <MetricsStrip metrics={metrics} isLoading={isStatusLoading} showHeader={false} />
          </div>
        </div>
      </section>

      <section className="mx-auto w-full max-w-6xl space-y-10 px-6">
        <div className="grid gap-8 md:grid-cols-12">
          <div className="md:col-span-6">
            <StatusAlertsCard onLeadSubmit={trackLeadSubmit} source="landing-status-card" />
          </div>
          <div className="md:col-span-6 space-y-4 rounded-3xl border border-white/10 bg-white/5 p-6">
            <SectionHeader
              eyebrow="Operators"
              title="Ready for incident response and compliance"
              description="Everything you need to keep stakeholders informed from day zero."
            />
            <ul className="space-y-3 text-foreground/80">
              {OPERATOR_BULLETS.map((bullet) => (
                <li key={bullet} className="flex items-start gap-2 text-sm">
                  <span className="mt-1 inline-block h-2.5 w-2.5 rounded-full bg-primary" />
                  <span>{bullet}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <section className="mx-auto w-full max-w-6xl space-y-10 px-6">
        <FaqSection items={FAQ_ITEMS} columns={2} />
      </section>

      <section className="relative w-full rounded-3xl bg-gradient-to-r from-primary/15 via-background to-primary/10 px-6 pb-16 pt-4">
        <div className="mx-auto w-full max-w-6xl rounded-3xl border border-primary/20 bg-white/5 px-6 py-10">
          <CtaBand config={ctaBandConfig} onCtaClick={trackCtaClick} />
        </div>
      </section>
    </div>
  );
}
