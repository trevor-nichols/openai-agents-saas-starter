"use client";

import { Marquee, MarqueeContent, MarqueeFade, MarqueeItem } from '@/components/ui/marquee';
import { SectionHeader } from '@/components/ui/foundation';
import type { LogoItem } from '../types';

interface SocialProofMarqueeProps {
  logos: LogoItem[];
}

export function SocialProofMarquee({ logos }: SocialProofMarqueeProps) {
  if (!logos.length) return null;

  return (
    <section className="relative w-full rounded-3xl bg-gradient-to-r from-white/5 via-primary/5 to-white/5 px-6 py-10">
      <div className="mx-auto w-full max-w-6xl space-y-6">
        <SectionHeader
          eyebrow="Trusted by teams shipping agents"
          title="Move faster without rebuilding the foundation"
          description="Product, platform, and ops teams are already launching on this starter."
        />
        <div className="relative rounded-2xl border border-white/10 bg-background/70 px-4 py-3 shadow-sm">
          <Marquee>
            <MarqueeFade side="left" />
            <MarqueeContent speed={40} pauseOnHover loop={0} gradient={false}>
              {logos.map((logo) => (
                <MarqueeItem key={logo} className="mx-4">
                  <span className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-foreground/70">
                    {logo}
                  </span>
                </MarqueeItem>
              ))}
            </MarqueeContent>
            <MarqueeFade side="right" />
          </Marquee>
        </div>
      </div>
    </section>
  );
}
