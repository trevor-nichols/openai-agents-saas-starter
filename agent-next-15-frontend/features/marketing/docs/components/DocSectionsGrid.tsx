import Link from 'next/link';

import { Badge } from '@/components/ui/badge';
import { GlassPanel, SectionHeader } from '@/components/ui/foundation';

import type { DocSectionEntry } from '../types';

interface DocSectionsGridProps {
  sections: DocSectionEntry[];
  onCtaClick: (meta: { location: string; cta: DocSectionEntry['cta'] }) => void;
}

export function DocSectionsGrid({ sections, onCtaClick }: DocSectionsGridProps) {
  return (
    <section className="space-y-6">
      <SectionHeader
        eyebrow="Documentation pillars"
        title="Find the right guide for your team"
        description="Every pillar has focused runbooks, so onboarding stays fast."
      />
      <div className="grid gap-4 md:grid-cols-2">
        {sections.map((section) => (
          <GlassPanel key={section.id} id={section.id} className="space-y-4 border border-white/10">
            <div className="flex items-center gap-3">
              <Badge variant="secondary">{section.badge}</Badge>
              <h3 className="text-lg font-semibold text-foreground">{section.title}</h3>
            </div>
            <p className="text-sm text-foreground/70">{section.summary}</p>
            <ul className="space-y-2 text-sm text-foreground/70">
              {section.bullets.map((bullet) => (
                <li key={`${section.id}-${bullet}`}>• {bullet}</li>
              ))}
            </ul>
            <Link
              className="text-sm font-semibold text-primary"
              href={section.cta.href}
              onClick={() => onCtaClick({ location: `docs-section-${section.id}`, cta: section.cta })}
            >
              {section.cta.label}
            </Link>
          </GlassPanel>
        ))}
      </div>
    </section>
  );
}
