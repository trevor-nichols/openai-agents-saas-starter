'use client';

import { useMemo } from 'react';
import { usePathname } from 'next/navigation';

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';
import { SectionHeader } from '@/components/ui/foundation/SectionHeader';

import type { AppNavItem } from './AppNavLinks';

interface AppPageHeadingProps {
  navItems: AppNavItem[];
  accountItems: AppNavItem[];
  subtitle: string;
}

export function AppPageHeading({ navItems, accountItems, subtitle }: AppPageHeadingProps) {
  const pathname = usePathname() ?? '';
  const allItems = useMemo(() => [...navItems, ...accountItems], [navItems, accountItems]);

  const active = useMemo(() => {
    return (
      allItems.find((item) => pathname === item.href || pathname.startsWith(`${item.href}/`)) ?? {
        href: '/dashboard',
        label: 'Dashboard',
      }
    );
  }, [allItems, pathname]);

  return (
    <div className="space-y-3">
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbPage className="text-xs font-semibold uppercase tracking-[0.3em] text-foreground/50">
              Acme Console
            </BreadcrumbPage>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage className="text-sm font-semibold text-foreground">{active.label}</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      <SectionHeader title={active.label} description={subtitle} size="compact" />
    </div>
  );
}
