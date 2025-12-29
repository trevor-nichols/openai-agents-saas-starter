'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

import { GlassPanel } from '@/components/ui/foundation';
import { cn } from '@/lib/utils';

const NAV_ITEMS = [
  {
    href: '/settings/team',
    label: 'Team',
    description: 'Members, roles, and invites.',
  },
  {
    href: '/settings/tenant',
    label: 'Tenant',
    description: 'Billing contacts, webhooks, and flags.',
  },
  {
    href: '/settings/access',
    label: 'Signup guardrails',
    description: 'Signup invites and approvals.',
  },
];

export function SettingsNav() {
  const pathname = usePathname() ?? '';

  return (
    <GlassPanel className="p-4">
      <div className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.25em] text-foreground/50">Settings</p>
        <nav className="flex gap-2 overflow-x-auto lg:flex-col">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex min-w-[200px] flex-col gap-1 rounded-xl border border-transparent px-3 py-2 text-sm transition-colors',
                  isActive
                    ? 'border-primary/30 bg-primary/10 text-foreground'
                    : 'text-foreground/70 hover:border-white/10 hover:bg-white/5',
                )}
              >
                <span className="font-medium">{item.label}</span>
                <span className="text-xs text-foreground/60">{item.description}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </GlassPanel>
  );
}
