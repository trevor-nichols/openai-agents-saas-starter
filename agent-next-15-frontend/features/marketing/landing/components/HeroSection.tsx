'use client';

import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { GlassPanel, InlineTag } from '@/components/ui/foundation';

import type { CtaLink } from '@/features/marketing/types';
import type { HeroCopy, StatusSummary } from '../types';

interface HeroSectionProps {
  copy: HeroCopy;
  statusSummary: StatusSummary | null;
  onCtaClick: (meta: { location: string; cta: CtaLink }) => void;
}

export function HeroSection({ copy, statusSummary, onCtaClick }: HeroSectionProps) {
  const handleClick = (cta: CtaLink, location: string) => () => {
    onCtaClick({ cta, location });
  };

  return (
    <section className="grid gap-8 lg:grid-cols-[1.2fr,0.8fr] lg:items-center">
      <div className="space-y-6">
        <InlineTag tone="default">{copy.eyebrow}</InlineTag>
        <h1 className="text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
          {copy.title}
        </h1>
        <p className="text-lg text-foreground/70">{copy.description}</p>
        <div className="flex flex-wrap gap-4">
          <Button size="lg" onClick={handleClick(copy.primaryCta, 'hero-primary')} asChild>
            <Link href={copy.primaryCta.href}>{copy.primaryCta.label}</Link>
          </Button>
          <Button
            size="lg"
            variant="outline"
            onClick={handleClick(copy.secondaryCta, 'hero-secondary')}
            asChild
          >
            <Link href={copy.secondaryCta.href}>{copy.secondaryCta.label}</Link>
          </Button>
        </div>
      </div>

      <GlassPanel className="space-y-3">
        <p className="text-sm font-semibold uppercase tracking-[0.3em] text-foreground/50">
          Deployment snapshot
        </p>
        {statusSummary ? (
          <>
            <div className="flex items-center gap-3">
              <InlineTag tone={statusSummary.state.toLowerCase().includes('oper') ? 'positive' : 'warning'}>
                {statusSummary.state}
              </InlineTag>
              <p className="text-sm text-foreground/60">Updated {statusSummary.updatedAt}</p>
            </div>
            <p className="text-base text-foreground/80">{statusSummary.description}</p>
          </>
        ) : (
          <p className="text-base text-foreground/70">
            Live status, billing telemetry, and agents SDK sessions all ship ready for your brand.
          </p>
        )}
        <Button variant="ghost" className="px-0" asChild onClick={handleClick(copy.secondaryCta, 'hero-status')}>
          <Link href="/status">Explore status</Link>
        </Button>
      </GlassPanel>
    </section>
  );
}
