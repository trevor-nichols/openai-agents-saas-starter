import Link from 'next/link';
import { ArrowUpRight } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { GlassPanel } from '@/components/ui/foundation';

import type { QuickAction } from '../types';

interface QuickActionsProps {
  actions: QuickAction[];
}

export function QuickActions({ actions }: QuickActionsProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {actions.map((action) => {
        const Icon = action.icon;
        return (
          <GlassPanel key={action.id} className="flex h-full flex-col gap-4 border-white/5 bg-white/5">
            <div className="flex items-center gap-3">
              <div className="rounded-full border border-white/10 bg-white/10 p-2 text-foreground">
                <Icon className="h-4 w-4" />
              </div>
              <div>
                <p className="text-sm font-semibold text-foreground">{action.label}</p>
                <p className="text-xs text-foreground/60">{action.description}</p>
              </div>
            </div>

            <Button asChild variant="ghost" className="mt-auto justify-start px-0 text-foreground/80">
              <Link href={action.href} className="inline-flex items-center gap-1">
                Go
                <ArrowUpRight className="h-4 w-4" />
              </Link>
            </Button>
          </GlassPanel>
        );
      })}
    </div>
  );
}
