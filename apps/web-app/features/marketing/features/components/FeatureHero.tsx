import Link from 'next/link';
import { ArrowDown } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

import type { CtaLink } from '@/features/marketing/types';
import type { FeatureNavItem } from '../types';

interface FeatureHeroProps {
  eyebrow: string;
  title: string;
  description: string;
  primaryCta: CtaLink;
  secondaryCta: CtaLink;
  navItems: FeatureNavItem[];
  onCtaClick: (meta: { location: string; cta: CtaLink }) => void;
}

export function FeatureHero({ eyebrow, title, description, primaryCta, secondaryCta, navItems, onCtaClick }: FeatureHeroProps) {
  const handleClick = (cta: CtaLink, location: string) => () => onCtaClick({ location, cta });

  return (
    <div className="relative z-10 flex flex-col items-center text-center space-y-8 py-12 md:py-24">
      {/* Ambient background glow */}
      <div className="absolute top-1/2 left-1/2 -z-10 h-[300px] w-[600px] -translate-x-1/2 -translate-y-1/2 opacity-15 bg-gradient-to-r from-primary via-indigo-500 to-purple-500 blur-[120px]" />

      <Badge 
        variant="outline" 
        className="px-4 py-1.5 text-xs font-semibold uppercase tracking-widest text-muted-foreground border-primary/20 bg-primary/5 rounded-full"
      >
        {eyebrow}
      </Badge>

      <div className="max-w-4xl space-y-6">
        <h1 className="text-5xl font-bold tracking-tight text-foreground sm:text-7xl md:text-8xl">
          <span className="bg-gradient-to-b from-foreground to-foreground/70 bg-clip-text supports-[background-clip:text]:text-transparent">
            {title}
          </span>
        </h1>
        <p className="text-xl text-muted-foreground leading-relaxed max-w-2xl mx-auto">
          {description}
        </p>
      </div>

      <div className="flex flex-wrap justify-center gap-4">
        <Button size="lg" className="h-12 px-8 rounded-full text-base" onClick={handleClick(primaryCta, 'features-hero-primary')} asChild>
          <Link href={primaryCta.href}>{primaryCta.label}</Link>
        </Button>
        <Button size="lg" variant="outline" className="h-12 px-8 rounded-full text-base" onClick={handleClick(secondaryCta, 'features-hero-secondary')} asChild>
          <Link href={secondaryCta.href}>{secondaryCta.label}</Link>
        </Button>
      </div>

      <div className="mt-16 w-full max-w-2xl border-t border-border/40 pt-10">
        <p className="mb-6 text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60">
          Explore Capabilities
        </p>
        <nav className="flex flex-wrap justify-center gap-3">
          {navItems.map((item) => {
            const navCta: CtaLink = { label: item.label, href: `#${item.id}`, intent: 'secondary' };
            return (
              <Button
                key={item.id}
                variant="ghost"
                size="sm"
                asChild
                className="group rounded-full text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-all"
                onClick={() => onCtaClick({ location: `features-nav-${item.id}`, cta: navCta })}
              >
                <Link href={navCta.href} className="flex items-center gap-2">
                  {item.label}
                  <ArrowDown className="h-3 w-3 opacity-0 -translate-y-1 transition-all group-hover:opacity-50 group-hover:translate-y-0" />
                </Link>
              </Button>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
