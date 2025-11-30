"use client";

import Link from 'next/link';

import { HeroGeometric } from '@/components/ui/hero';
import { Button } from '@/components/ui/button';
import { GlassPanel } from '@/components/ui/foundation';

import type { CtaLink } from '@/features/marketing/types';
import type { HeroCopy, StatusSummary } from '../types';

interface HeroSectionProps {
  copy: HeroCopy;
  statusSummary: StatusSummary | null;
  onCtaClick: (meta: { location: string; cta: CtaLink }) => void;
}

export function HeroSection({ copy, statusSummary, onCtaClick }: HeroSectionProps) {
  const statusCta: CtaLink = {
    label: 'Explore status',
    href: '/status',
    intent: 'secondary',
  };

  const [title1, title2] = splitTitle(copy.title);

  const handleClick = (cta: CtaLink, location: string) => () => {
    onCtaClick({ cta, location });
  };

  return (
    <section className="relative isolate w-screen left-1/2 right-1/2 -ml-[50vw] -mr-[50vw] overflow-hidden pt-4 lg:pt-0">
      <HeroGeometric
        title1={title1}
        title2={title2}
        description={copy.description}
        className="min-h-[92vh]"
        actions={
          <>
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
          </>
        }
        footer={
          <GlassPanel className="space-y-3 border border-white/10 bg-white/5 backdrop-blur w-full max-w-xl">
            <p className="text-sm font-semibold uppercase tracking-[0.3em] text-foreground/50">
              Deployment snapshot
            </p>
            {statusSummary ? (
              <>
                <div className="flex items-center gap-3">
                  <span
                    className="inline-flex items-center rounded-full bg-primary/10 px-2 py-1 text-xs font-semibold uppercase tracking-wide text-primary"
                    role="status"
                  >
                    {statusSummary.state}
                  </span>
                  <p className="text-sm text-foreground/60">Updated {statusSummary.updatedAt}</p>
                </div>
                <p className="text-base text-foreground/80">{statusSummary.description}</p>
              </>
            ) : (
              <p className="text-base text-foreground/70">
                Live status, billing telemetry, and agents SDK sessions all ship ready for your brand.
              </p>
            )}
            <Button variant="ghost" className="px-0" asChild onClick={handleClick(statusCta, 'hero-status')}>
              <Link href={statusCta.href}>{statusCta.label}</Link>
            </Button>
          </GlassPanel>
        }
      />
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-background via-background/50 to-transparent" />
    </section>
  );
}

function splitTitle(title: string): [string, string] {
  const words = title.split(' ');
  if (words.length <= 3) {
    return [title, title];
  }
  const mid = Math.ceil(words.length / 2);
  return [words.slice(0, mid).join(' '), words.slice(mid).join(' ')];
}
