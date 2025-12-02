import Link from 'next/link';
import { ArrowUpRight } from 'lucide-react';

import type { QuickAction } from '../types';

interface QuickActionsProps {
  actions: QuickAction[];
}

export function QuickActions({ actions }: QuickActionsProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
      {actions.map((action) => {
        const Icon = action.icon;
        return (
          <Link
            key={action.id}
            href={action.href}
            className="group relative flex flex-col gap-3 rounded-xl border border-white/5 bg-white/5 p-4 transition-all hover:border-white/20 hover:bg-white/10"
          >
            <div className="flex items-start justify-between">
              <div className="rounded-lg bg-white/5 p-2 text-muted-foreground transition-colors group-hover:text-foreground">
                <Icon className="h-5 w-5" />
              </div>
              <ArrowUpRight className="h-4 w-4 text-muted-foreground opacity-0 transition-all group-hover:opacity-100" />
            </div>
            
            <div className="space-y-1">
              <p className="font-medium leading-none text-foreground">{action.label}</p>
              <p className="line-clamp-2 text-xs text-muted-foreground">
                {action.description}
              </p>
            </div>
          </Link>
        );
      })}
    </div>
  );
}
