'use client';

import { GlassPanel, SectionHeader } from '@/components/ui/foundation';
import { Check, ShieldCheck } from 'lucide-react';

import { ACCESS_REQUEST_COPY } from '../constants';

export function AccessRequestHero() {
  return (
    <section className="space-y-8">
      <SectionHeader
        eyebrow={ACCESS_REQUEST_COPY.eyebrow}
        title={ACCESS_REQUEST_COPY.title}
        description={ACCESS_REQUEST_COPY.description}
      />
      <GlassPanel className="space-y-6 p-8">
        <div className="flex items-center gap-2.5 border-b border-border/40 pb-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <h3 className="text-lg font-semibold text-foreground">
            Why we vet requests
          </h3>
        </div>
        <ul className="grid gap-4 sm:grid-cols-1">
          {ACCESS_REQUEST_COPY.talkingPoints.map((point) => (
            <li key={point} className="flex items-start gap-3">
              <div className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                <Check className="h-3 w-3" />
              </div>
              <span className="text-sm leading-relaxed text-muted-foreground">
                {point}
              </span>
            </li>
          ))}
        </ul>
      </GlassPanel>
    </section>
  );
}
