import Link from 'next/link';

import { GlassPanel } from '@/components/ui/foundation/GlassPanel';
import { SectionHeader } from '@/components/ui/foundation/SectionHeader';
import { cn } from '@/lib/utils';

import { AppNavLinks, type AppNavItem } from './AppNavLinks';

interface AppSidebarProps {
  navItems: AppNavItem[];
  accountItems: AppNavItem[];
  brandHref?: string;
  brandLabel?: string;
  description?: string;
  accountDescription?: string;
  className?: string;
}

export function AppSidebar({
  navItems,
  accountItems,
  brandHref = '/dashboard',
  brandLabel = 'Acme',
  description = 'Operate your AI agent stack with confidence.',
  accountDescription = 'Profile, guardrails, and tenant controls',
  className,
}: AppSidebarProps) {
  return (
    <aside
      className={cn(
        'relative hidden w-[300px] flex-col border-r border-white/5 bg-transparent px-4 py-6 lg:flex',
        className
      )}
    >
      <GlassPanel className="flex h-full flex-col gap-8 bg-background/70">
        <div>
          <Link href={brandHref} className="text-xl font-semibold tracking-tight">
            {brandLabel}
          </Link>
          <p className="mt-2 text-sm text-foreground/60">{description}</p>
        </div>

        <nav aria-label="Primary navigation" className="text-sm font-medium">
          <AppNavLinks items={navItems} />
        </nav>

        <div className="mt-auto space-y-3">
          <SectionHeader eyebrow="Account" title="Manage workspace" description={accountDescription} size="compact" />
          <nav aria-label="Account navigation" className="text-sm">
            <AppNavLinks items={accountItems} />
          </nav>
        </div>
      </GlassPanel>
    </aside>
  );
}

