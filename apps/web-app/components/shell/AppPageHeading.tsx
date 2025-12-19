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
  
  const active = useMemo(() => {
    const flatten = (items: AppNavItem[]): AppNavItem[] => {
      return items.reduce((acc, item) => {
        acc.push(item);
        if (item.items) {
          acc.push(...flatten(item.items));
        }
        return acc;
      }, [] as AppNavItem[]);
    };

    const allItems = flatten([...navItems, ...accountItems]);

    return (
      allItems.find((item) => pathname === item.href || pathname.startsWith(`${item.href}/`)) ?? {
        href: '/dashboard',
        label: 'Dashboard',
      }
    );
  }, [navItems, accountItems, pathname]);

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
