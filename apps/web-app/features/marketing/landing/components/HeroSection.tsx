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
          <GlassPanel className="flex flex-col gap-4 w-full max-w-lg rounded-3xl border border-white/10 bg-background/40 p-6 shadow-2xl backdrop-blur-xl">
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <p className="text-xs font-bold uppercase tracking-wider text-primary">
                Deployment snapshot
              </p>
              {statusSummary ? (
                <span
                  className="flex h-6 items-center rounded-full bg-emerald-500/15 px-2.5 text-[10px] font-bold uppercase tracking-wide text-emerald-500"
                  role="status"
                >
                  {statusSummary.state}
                </span>
              ) : null}
            </div>
            
            <div className="space-y-4">
              {statusSummary ? (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    <p>Updated {statusSummary.updatedAt}</p>
                  </div>
                  <p className="text-sm text-muted-foreground leading-relaxed">{statusSummary.description}</p>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Live status, billing telemetry, and agents SDK sessions all ship ready for your brand.
                </p>
              )}
              
              <Button 
                className="w-full rounded-full bg-primary/10 text-primary hover:bg-primary/20 hover:text-primary font-semibold h-10 shadow-none" 
                onClick={handleClick(statusCta, 'hero-status')}
                asChild
              >
                <Link href={statusCta.href}>{statusCta.label}</Link>
              </Button>
            </div>
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
