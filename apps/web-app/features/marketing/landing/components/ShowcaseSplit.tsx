import { GlassPanel, SectionHeader } from '@/components/ui/foundation';
import { ShowcaseTabs } from '@/features/marketing/features/components/ShowcaseTabs';

import type { ShowcaseTab } from '@/features/marketing/features/types';

interface ShowcaseSplitProps {
  tabs: ShowcaseTab[];
}

export function ShowcaseSplit({ tabs }: ShowcaseSplitProps) {
  if (!tabs.length) return null;

  return (
    <section className="mx-auto w-full max-w-6xl space-y-10 px-6">
      <SectionHeader
        eyebrow="Product walkthrough"
        title="See how the starter behaves before you clone it"
        description="Deep-dive into the core surfaces—agents, billing, and ops—without juggling multiple demos."
      />

      <div className="grid gap-8 md:grid-cols-12">
        <div className="md:col-span-7">
          <ShowcaseTabs tabs={tabs} />
        </div>
        <div className="md:col-span-5">
          <GlassPanel className="relative h-full min-h-[320px] overflow-hidden border border-white/10 bg-gradient-to-br from-primary/10 via-background to-background">
            <div className="absolute inset-0 opacity-60" style={{ backgroundImage: 'radial-gradient(circle at 20% 20%, rgba(100,108,255,0.25), transparent 40%), radial-gradient(circle at 80% 40%, rgba(99,223,255,0.2), transparent 35%), radial-gradient(circle at 50% 80%, rgba(255,255,255,0.12), transparent 45%)' }} />
            <div className="relative flex h-full flex-col justify-between p-6 text-foreground/80">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-foreground/60">Workspace preview</p>
                <h3 className="mt-2 text-2xl font-semibold text-foreground">Agent console, ready to brand</h3>
                <p className="mt-2 text-sm text-foreground/70">
                  Streamed chat, tool traces, plan banners, and audit exports come prewired. Swap the theme and drop in your logo.
                </p>
              </div>
              <div className="mt-6 grid grid-cols-2 gap-3 text-sm text-foreground/80">
                <span className="rounded-lg bg-white/5 px-3 py-2">Live SSE streams</span>
                <span className="rounded-lg bg-white/5 px-3 py-2">Tool registry insights</span>
                <span className="rounded-lg bg-white/5 px-3 py-2">Billing-aware UI states</span>
                <span className="rounded-lg bg-white/5 px-3 py-2">Exportable transcripts</span>
              </div>
            </div>
          </GlassPanel>
        </div>
      </div>
    </section>
  );
}
