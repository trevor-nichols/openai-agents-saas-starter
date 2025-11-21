import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { GlassPanel, InlineTag } from '@/components/ui/foundation';

import type { CtaLink } from '@/features/marketing/types';

interface PricingHeroProps {
  eyebrow: string;
  title: string;
  description: string;
  primaryCta: CtaLink;
  secondaryCta: CtaLink;
  onCtaClick: (meta: { location: string; cta: CtaLink }) => void;
}

export function PricingHero({ eyebrow, title, description, primaryCta, secondaryCta, onCtaClick }: PricingHeroProps) {
  const handleClick = (cta: CtaLink, location: string) => () => onCtaClick({ location, cta });

  return (
    <section className="space-y-6">
      <InlineTag tone="default">{eyebrow}</InlineTag>
      <div className="space-y-4">
        <h1 className="text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">{title}</h1>
        <p className="text-lg text-foreground/70">{description}</p>
      </div>
      <div className="flex flex-wrap gap-4">
        <Button size="lg" onClick={handleClick(primaryCta, 'pricing-hero-primary')} asChild>
          <Link href={primaryCta.href}>{primaryCta.label}</Link>
        </Button>
        <Button size="lg" variant="outline" onClick={handleClick(secondaryCta, 'pricing-hero-secondary')} asChild>
          <Link href={secondaryCta.href}>{secondaryCta.label}</Link>
        </Button>
      </div>
      <GlassPanel className="space-y-2 border border-white/10">
        <p className="text-sm uppercase tracking-[0.3em] text-foreground/50">What’s included</p>
        <p className="text-sm text-foreground/70">
          GPT-5 agents workspace, billing automation, tenant settings, and observability are available on every tier.
        </p>
      </GlassPanel>
    </section>
  );
}
