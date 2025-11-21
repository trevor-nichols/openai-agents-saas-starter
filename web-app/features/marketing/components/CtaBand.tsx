import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { GlassPanel } from '@/components/ui/foundation';

import type { CtaConfig, CtaLink } from '@/features/marketing/types';

interface CtaBandProps {
  config: CtaConfig;
  onCtaClick: (meta: { location: string; cta: CtaLink }) => void;
}

export function CtaBand({ config, onCtaClick }: CtaBandProps) {
  const handleClick = (cta: CtaLink, location: string) => () => onCtaClick({ location, cta });

  return (
    <GlassPanel className="flex flex-col gap-6 border border-primary/30 bg-primary/5 px-8 py-10 text-center md:text-left">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-primary">{config.eyebrow ?? 'Launch'}</p>
        <h2 className="text-3xl font-semibold text-foreground">{config.title}</h2>
        <p className="mt-2 text-foreground/70">{config.description}</p>
      </div>
      <div className="flex flex-col gap-4 md:flex-row">
        <Button size="lg" onClick={handleClick(config.primaryCta, 'cta-primary')} asChild>
          <Link href={config.primaryCta.href}>{config.primaryCta.label}</Link>
        </Button>
        <Button size="lg" variant="secondary" onClick={handleClick(config.secondaryCta, 'cta-secondary')} asChild>
          <Link href={config.secondaryCta.href}>{config.secondaryCta.label}</Link>
        </Button>
      </div>
    </GlassPanel>
  );
}
