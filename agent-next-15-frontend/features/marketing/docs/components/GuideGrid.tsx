import { GlassPanel } from '@/components/ui/foundation';
import { Button } from '@/components/ui/button';

import type { DocGuideCard } from '../types';

interface GuideGridProps {
  guides: DocGuideCard[];
}

export function GuideGrid({ guides }: GuideGridProps) {
  if (!guides.length) {
    return null;
  }

  return (
    <section className="space-y-6">
      <div className="flex flex-col gap-2">
        <p className="text-xs uppercase tracking-[0.3em] text-foreground/50">Guides</p>
        <h2 className="text-3xl font-semibold text-foreground">Featured playbooks</h2>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {guides.map((guide) => (
          <GlassPanel key={guide.title} className="space-y-3 border border-white/10">
            <div className="flex items-center gap-3">
              <guide.icon className="h-5 w-5 text-foreground/60" />
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-foreground/50">{guide.badge}</p>
                <h3 className="text-lg font-semibold text-foreground">{guide.title}</h3>
              </div>
            </div>
            <p className="text-sm text-foreground/70">{guide.description}</p>
            <p className="text-xs text-foreground/60">{guide.minutes} • {guide.updated}</p>
            <Button variant="outline" asChild>
              <a href={guide.href} target="_blank" rel="noreferrer noopener">
                Open guide
              </a>
            </Button>
          </GlassPanel>
        ))}
      </div>
    </section>
  );
}
