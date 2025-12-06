import { GlassPanel } from '@/components/ui/foundation';
import { ShowcaseTabs } from '@/features/marketing/features/components/ShowcaseTabs';

import type { ShowcaseTab } from '@/features/marketing/features/types';

interface ShowcaseSplitProps {
  tabs: ShowcaseTab[];
}

export function ShowcaseSplit({ tabs }: ShowcaseSplitProps) {
  if (!tabs.length) return null;

  return (
    <section className="mx-auto w-full max-w-6xl px-6">
      <div className="grid gap-8 md:grid-cols-12">
        <div className="md:col-span-7">
          <ShowcaseTabs tabs={tabs} />
        </div>
        <div className="md:col-span-5 pt-24">
          <GlassPanel className="relative h-full min-h-[320px] overflow-hidden bg-primary/5 p-8">
            <div className="absolute inset-0 opacity-60" style={{ backgroundImage: 'radial-gradient(circle at 20% 20%, rgba(100,108,255,0.25), transparent 40%), radial-gradient(circle at 80% 40%, rgba(99,223,255,0.2), transparent 35%), radial-gradient(circle at 50% 80%, rgba(255,255,255,0.12), transparent 45%)' }} />
            <div className="relative flex h-full flex-col justify-between text-foreground/80">
              <div className="space-y-2">
                <p className="text-xs font-bold uppercase tracking-wider text-primary">Workspace preview</p>
                <h3 className="text-2xl font-bold tracking-tight text-foreground">Agent console, ready to brand</h3>
                <p className="text-base text-muted-foreground leading-relaxed">
                  Streamed chat, tool traces, plan banners, and audit exports come prewired. Swap the theme and drop in your logo.
                </p>
              </div>
              <div className="mt-6 grid grid-cols-2 gap-3">
                <span className="flex items-center justify-center rounded-full bg-background/50 px-3 py-1.5 text-xs font-medium text-foreground shadow-sm">Live SSE streams</span>
                <span className="flex items-center justify-center rounded-full bg-background/50 px-3 py-1.5 text-xs font-medium text-foreground shadow-sm">Tool registry insights</span>
                <span className="flex items-center justify-center rounded-full bg-background/50 px-3 py-1.5 text-xs font-medium text-foreground shadow-sm">Billing-aware UI states</span>
                <span className="flex items-center justify-center rounded-full bg-background/50 px-3 py-1.5 text-xs font-medium text-foreground shadow-sm">Exportable transcripts</span>
              </div>
            </div>
          </GlassPanel>
        </div>
      </div>
    </section>
  );
}
