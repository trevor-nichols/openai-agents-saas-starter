import { GlassPanel } from '@/components/ui/foundation';
import { Button } from '@/components/ui/button';
import { ArrowUpRight } from 'lucide-react';

import type { DocResourceLink } from '../types';

interface ResourceLinksProps {
  resources: DocResourceLink[];
}

export function ResourceLinks({ resources }: ResourceLinksProps) {
  if (!resources.length) {
    return null;
  }

  return (
    <section className="space-y-6">
      <div className="flex flex-col gap-2">
        <p className="text-xs uppercase tracking-[0.3em] text-foreground/50">Resources</p>
        <h2 className="text-3xl font-semibold text-foreground">Core references</h2>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {resources.map((resource) => (
          <GlassPanel key={resource.label} className="space-y-3 border border-white/10">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.3em] text-foreground/50">{resource.badge}</p>
                <h3 className="text-lg font-semibold text-foreground">{resource.label}</h3>
              </div>
              <Button size="icon" variant="ghost" asChild>
                <a href={resource.href} target="_blank" rel="noreferrer noopener">
                  <ArrowUpRight className="h-4 w-4" />
                </a>
              </Button>
            </div>
            <p className="text-sm text-foreground/70">{resource.description}</p>
          </GlassPanel>
        ))}
      </div>
    </section>
  );
}
