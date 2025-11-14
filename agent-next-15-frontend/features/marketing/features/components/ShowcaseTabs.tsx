import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { GlassPanel } from '@/components/ui/foundation';

import type { ShowcaseTab } from '../types';

interface ShowcaseTabsProps {
  tabs: ShowcaseTab[];
}

export function ShowcaseTabs({ tabs }: ShowcaseTabsProps) {
  if (!tabs.length) {
    return null;
  }

  const defaultTab = tabs[0]?.id ?? 'agents';

  return (
    <section className="space-y-6">
      <div className="flex flex-col gap-2">
        <p className="text-xs uppercase tracking-[0.3em] text-foreground/50">Deep dive</p>
        <h2 className="text-3xl font-semibold text-foreground">See how each module behaves</h2>
      </div>
      <Tabs defaultValue={defaultTab} className="space-y-4">
        <TabsList>
          {tabs.map((tab) => (
            <TabsTrigger key={tab.id} value={tab.id} className="text-sm">
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>
        {tabs.map((tab) => (
          <TabsContent key={tab.id} value={tab.id} className="focus:outline-none">
            <GlassPanel className="space-y-4 border border-white/10">
              <div>
                <h3 className="text-2xl font-semibold text-foreground">{tab.title}</h3>
                <p className="text-foreground/70">{tab.description}</p>
              </div>
              <ul className="grid gap-3 md:grid-cols-3">
                {tab.bullets.map((bullet) => (
                  <li key={`${tab.id}-${bullet}`} className="rounded-xl border border-white/10 bg-white/5 p-4 text-sm text-foreground/80">
                    {bullet}
                  </li>
                ))}
              </ul>
            </GlassPanel>
          </TabsContent>
        ))}
      </Tabs>
    </section>
  );
}
