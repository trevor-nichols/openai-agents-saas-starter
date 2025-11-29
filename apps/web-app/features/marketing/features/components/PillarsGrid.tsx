import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { GlassPanel, SectionHeader } from '@/components/ui/foundation';

import type { FeaturePillar } from '../types';

interface PillarsGridProps {
  pillars: FeaturePillar[];
  onCtaClick: (meta: { location: string; cta: FeaturePillar['cta'] }) => void;
}

export function PillarsGrid({ pillars, onCtaClick }: PillarsGridProps) {
  return (
    <section className="space-y-6" id="pillars">
      <SectionHeader
        eyebrow="Pillars"
        title="Everything you need to ship an AI agent SaaS"
        description="Each module ships in its own feature directory so you can customize without touching the shared foundation."
      />
      <div className="grid gap-4 md:grid-cols-3">
        {pillars.map((pillar) => (
          <GlassPanel key={pillar.id} id={pillar.id} className="space-y-4 border border-white/10">
            <div className="flex items-center gap-3">
              <pillar.icon className="h-5 w-5 text-foreground/70" />
              <div>
                <h3 className="text-lg font-semibold text-foreground">{pillar.title}</h3>
                <p className="text-sm text-foreground/70">{pillar.description}</p>
              </div>
            </div>
            <ul className="space-y-2 text-sm text-foreground/70">
              {pillar.bullets.map((bullet) => (
                <li key={`${pillar.id}-${bullet}`}>• {bullet}</li>
              ))}
            </ul>
            <Button variant="ghost" className="px-0" asChild>
              <Link href={pillar.cta.href} onClick={() => onCtaClick({ location: `pillar-${pillar.id}`, cta: pillar.cta })}>
                {pillar.cta.label}
              </Link>
            </Button>
          </GlassPanel>
        ))}
      </div>
    </section>
  );
}
