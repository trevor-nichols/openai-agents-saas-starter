'use client';

import { GlassPanel, SectionHeader } from '@/components/ui/foundation';

import { ACCESS_REQUEST_COPY } from '../constants';

export function AccessRequestHero() {
  return (
    <section className="space-y-6">
      <SectionHeader
        eyebrow={ACCESS_REQUEST_COPY.eyebrow}
        title={ACCESS_REQUEST_COPY.title}
        description={ACCESS_REQUEST_COPY.description}
      />
      <GlassPanel className="space-y-4">
        <p className="text-sm font-semibold uppercase tracking-[0.3em] text-foreground/50">
          Why we vet requests
        </p>
        <ul className="list-disc space-y-2 pl-5 text-sm text-foreground/70">
          {ACCESS_REQUEST_COPY.talkingPoints.map((point) => (
            <li key={point}>{point}</li>
          ))}
        </ul>
      </GlassPanel>
    </section>
  );
}
