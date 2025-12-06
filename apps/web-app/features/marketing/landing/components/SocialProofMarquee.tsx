"use client";

import { Marquee, MarqueeContent, MarqueeItem } from '@/components/ui/marquee';
import type { LogoItem } from '../types';

interface SocialProofMarqueeProps {
  logos: LogoItem[];
}

export function SocialProofMarquee({ logos }: SocialProofMarqueeProps) {
  if (!logos.length) return null;

  return (
    <section className="w-full py-12">
      <div className="mx-auto w-full max-w-6xl px-6">
        <p className="mb-8 text-center text-sm font-bold uppercase tracking-wider text-muted-foreground">
          Trusted by teams shipping agents
        </p>
        <div className="relative w-full overflow-hidden [mask-image:_linear-gradient(to_right,transparent_0,_black_128px,_black_calc(100%-128px),transparent_100%)]">
          <Marquee>
            <MarqueeContent speed={30} pauseOnHover loop={0} gradient={false}>
              {logos.map((logo) => (
                <MarqueeItem key={logo} className="mx-8">
                  <span className="text-xl font-bold text-muted-foreground/40 transition-colors hover:text-foreground cursor-default select-none">
                    {logo}
                  </span>
                </MarqueeItem>
              ))}
            </MarqueeContent>
          </Marquee>
        </div>
      </div>
    </section>
  );
}
