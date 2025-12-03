import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { GlassPanel, SectionHeader } from '@/components/ui/foundation';

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
    <section className="space-y-8">
      <SectionHeader
        eyebrow="Product walkthrough"
        title="See how the starter behaves before you clone it"
        description="Deep-dive into the core surfaces—agents, billing, and ops—without juggling multiple demos."
      />
      <Tabs defaultValue={defaultTab} className="space-y-8">
        <TabsList className="w-full grid grid-cols-3 bg-muted/30 p-1 rounded-full h-auto">
          {tabs.map((tab) => (
            <TabsTrigger key={tab.id} value={tab.id} className="rounded-full py-2.5 text-sm font-medium data-[state=active]:bg-background data-[state=active]:shadow-sm">
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>
        {tabs.map((tab) => (
          <TabsContent key={tab.id} value={tab.id} className="focus:outline-none mt-0">
            <GlassPanel className="space-y-6 p-8">
              <div className="space-y-2">
                <h3 className="text-xl font-bold tracking-tight text-foreground">{tab.title}</h3>
                <p className="text-muted-foreground text-base leading-relaxed">{tab.description}</p>
              </div>
              <ul className="grid gap-4 md:grid-cols-3">
                {tab.bullets.map((bullet) => (
                  <li key={`${tab.id}-${bullet}`} className="flex items-center justify-center text-center rounded-2xl bg-muted/30 p-4 text-sm font-medium text-foreground/80 transition-colors hover:bg-muted/50">
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
